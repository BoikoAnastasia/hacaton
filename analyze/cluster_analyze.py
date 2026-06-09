"""
Кластерный LLM-анализ: семантическая группировка + Qwen только на представителях.
400k строк + --turbo → ~800 вызовов LLM → ~10-20 минут.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from llm_utils import analyze_batch, load_model
from columns import (
    COL_PROBLEM,
    COL_SEVERITY,
    COL_SUMMARY,
    RESULT_COLUMNS,
    attach_severity_labels,
    select_columns,
)
from problem_utils import refine_problem
from severity_utils import refine_severity
from summary_utils import make_summary_from_row, merge_llm_summary

TEXT_COLUMNS = ("Очищенный текст", "clean_text")
THEME_COLUMN = "Тема"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_MAX_CLUSTER_SIZE = 100
DEFAULT_MAX_LLM_CALLS = 800
ROWS_PER_CLUSTER_TARGET = 150


def parse_args():
    parser = argparse.ArgumentParser(description="Кластерный LLM-анализ")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--clusters", type=int, default=800, help="Верхний предел кластеров (≈ вызовов LLM)")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--max-cluster-size",
        type=int,
        default=DEFAULT_MAX_CLUSTER_SIZE,
        help="Макс. размер кластера; большие автоматически дробятся",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=DEFAULT_MAX_LLM_CALLS,
        help="Жёсткий лимит вызовов LLM (0 = без лимита)",
    )
    parser.add_argument(
        "--rows-per-cluster",
        type=int,
        default=ROWS_PER_CLUSTER_TARGET,
        help="Целевой размер кластера для расчёта числа групп",
    )
    parser.add_argument(
        "--turbo",
        action="store_true",
        help="Быстрый режим: мало кластеров, summary из темы, компактный LLM",
    )
    parser.add_argument(
        "--summary-source",
        choices=["theme", "llm", "hybrid"],
        default=None,
        help="theme=из колонки Тема (быстро), llm=из модели, hybrid=llm для представителей",
    )
    parser.add_argument(
        "--embed",
        choices=["tfidf", "sentence"],
        default="tfidf",
        help="tfidf=офлайн (по умолчанию), sentence=эмбеддинги (нужна загрузка модели)",
    )
    parser.add_argument("--embed-model", default=EMBED_MODEL)
    return parser.parse_args()


def detect_text_column(df):
    for col in TEXT_COLUMNS:
        if col in df.columns:
            return col
    raise KeyError(f"Нет колонки с текстом: {list(df.columns)}")


def vectorize_tfidf(texts):
    print("Векторизация TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.75,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)
    return matrix


def _slice_features(features, idxs, is_sparse):
    if is_sparse:
        return features[idxs]
    return features[idxs]


def cluster_indices(features, idxs, n_clusters, is_sparse, random_state=42):
    n = len(idxs)
    k = min(max(1, n_clusters), n)
    if k == 1:
        return np.zeros(n, dtype=int)

    sub_features = _slice_features(features, idxs, is_sparse)
    kmeans = MiniBatchKMeans(
        n_clusters=k,
        random_state=random_state,
        batch_size=min(4096, max(n, 256)),
        n_init=3,
    )
    return kmeans.fit_predict(sub_features)


def cluster_by_theme(df, features, n_clusters_total, is_sparse, theme_col=THEME_COLUMN):
    """Кластеризация внутри каждой темы — не смешиваем снег, ЖКХ, транспорт."""
    labels = np.full(len(df), -1, dtype=int)
    next_id = 0

    if theme_col not in df.columns:
        sub = cluster_indices(features, np.arange(len(df)), n_clusters_total, is_sparse)
        labels[:] = sub + next_id
        return labels

    themes = df[theme_col].fillna("").astype(str)
    groups = themes.groupby(themes).groups
    total = len(df)
    remaining = n_clusters_total
    theme_names = sorted(groups.keys(), key=lambda t: len(groups[t]), reverse=True)

    for i, theme in enumerate(theme_names):
        idxs = np.array(sorted(groups[theme]))
        n_theme = len(idxs)
        if i == len(theme_names) - 1:
            k = min(remaining, n_theme)
        else:
            k = max(1, round(n_clusters_total * n_theme / total))
            k = min(k, n_theme, max(1, remaining - (len(theme_names) - i - 1)))
        remaining -= k

        sub = cluster_indices(features, idxs, k, is_sparse, random_state=42 + next_id)
        for sl in np.unique(sub):
            labels[idxs[sub == sl]] = next_id
            next_id += 1

    return labels


def split_oversized_clusters(features, labels, max_size, is_sparse):
    """Дробит кластеры больше max_size — устраняет «суперкластеры» с одним summary."""
    labels = labels.copy()
    if max_size <= 0:
        return labels

    for iteration in range(20):
        sizes = pd.Series(labels).value_counts()
        if sizes.max() <= max_size:
            break

        changed = False
        next_id = int(labels.max()) + 1
        for label, size in sizes.items():
            if size <= max_size:
                continue

            idxs = np.where(labels == label)[0]
            changed = True
            n_sub = min(len(idxs), max(2, (len(idxs) + max_size - 1) // max_size))
            sub = cluster_indices(
                features,
                idxs,
                n_sub,
                is_sparse,
                random_state=1000 + iteration * 100 + int(label),
            )
            for sl in np.unique(sub):
                labels[idxs[sub == sl]] = next_id
                next_id += 1

        if not changed:
            break

    return labels


def print_cluster_stats(labels, max_size):
    sizes = pd.Series(labels).value_counts()
    print(
        f"Кластеров: {len(sizes)}, "
        f"средний размер: {sizes.mean():.1f}, "
        f"макс: {sizes.max()}, "
        f">{max_size}: {(sizes > max_size).sum()}"
    )


def effective_cluster_count(n, clusters_arg, max_llm_calls, rows_per_cluster):
    by_density = max(50, n // max(rows_per_cluster, 1))
    cap = max_llm_calls if max_llm_calls > 0 else clusters_arg
    return min(clusters_arg, by_density, cap, n)


def apply_turbo_defaults(args):
    if not args.turbo:
        return args
    args.clusters = min(args.clusters, DEFAULT_MAX_LLM_CALLS)
    args.max_llm_calls = min(args.max_llm_calls or DEFAULT_MAX_LLM_CALLS, DEFAULT_MAX_LLM_CALLS)
    args.max_cluster_size = max(args.max_cluster_size, 150)
    args.rows_per_cluster = max(args.rows_per_cluster, 150)
    if args.summary_source is None:
        args.summary_source = "theme"
    return args


def resolve_summary_source(args):
    if args.summary_source:
        return args.summary_source
    return "hybrid"


def vectorize_sentence(texts, model_name):
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Эмбеддинги ({model_name}, {device})...")
    model = SentenceTransformer(model_name, device=device)
    return model.encode(
        texts,
        batch_size=256,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def pick_representatives_tfidf(matrix, labels):
    representatives = {}
    for label in np.unique(labels):
        mask = labels == label
        idxs = np.where(mask)[0]
        cluster = matrix[idxs]
        centroid = cluster.mean(axis=0)
        scores = np.asarray(cluster @ centroid.T).ravel()
        representatives[label] = int(idxs[scores.argmax()])
    return representatives


def pick_representatives_dense(embeddings, labels):
    representatives = {}
    for label in np.unique(labels):
        mask = labels == label
        idxs = np.where(mask)[0]
        cluster_emb = embeddings[idxs]
        centroid = cluster_emb.mean(axis=0)
        dists = np.linalg.norm(cluster_emb - centroid, axis=1)
        representatives[label] = int(idxs[dists.argmin()])
    return representatives


def run_cluster_analysis(args):
    args = apply_turbo_defaults(args)
    summary_source = resolve_summary_source(args)
    compact_llm = summary_source == "theme"

    t0 = time.time()

    print(f"Загрузка {args.input}...")
    df = pd.read_excel(args.input)
    if args.limit > 0:
        df = df.head(args.limit).copy()

    text_col = detect_text_column(df)
    texts = df[text_col].fillna("").astype(str).tolist()
    n = len(texts)
    n_clusters = effective_cluster_count(n, args.clusters, args.max_llm_calls, args.rows_per_cluster)

    mode_label = "TURBO" if args.turbo else "cluster"
    print(
        f"Строк: {n}, режим: {mode_label}, кластеров: {n_clusters}, "
        f"summary: {summary_source}, batch: {args.batch_size}"
    )

    if args.embed == "sentence":
        features = vectorize_sentence(texts, args.embed_model)
        is_sparse = False
    else:
        features = vectorize_tfidf(texts)
        is_sparse = True
    print(f"Векторизация: {time.time() - t0:.1f}с")

    print("Кластеризация по темам...")
    labels = cluster_by_theme(df, features, n_clusters, is_sparse)
    labels = split_oversized_clusters(features, labels, args.max_cluster_size, is_sparse)
    df["cluster_id"] = labels
    print_cluster_stats(labels, args.max_cluster_size)
    print(f"Кластеризация: {time.time() - t0:.1f}с")

    if is_sparse:
        representatives = pick_representatives_tfidf(features, labels)
    else:
        representatives = pick_representatives_dense(features, labels)
    rep_indices = sorted(representatives.values())
    print(f"Представителей для LLM: {len(rep_indices)}")

    theme_col = "Тема" if "Тема" in df.columns else None
    group_col = "Группа тем" if "Группа тем" in df.columns else None
    themes_list = df[theme_col].tolist() if theme_col else [None] * n
    groups_list = df[group_col].tolist() if group_col else [None] * n

    rep_texts = [texts[i] for i in rep_indices]
    rep_themes = [df.iloc[i][theme_col] if theme_col else None for i in rep_indices]
    rep_groups = [df.iloc[i][group_col] if group_col else None for i in rep_indices]
    rep_labels = [df.iloc[i]["cluster_id"] for i in rep_indices]

    tokenizer, model = load_model()
    cluster_results = {}

    llm_start = time.time()
    for i in range(0, len(rep_texts), args.batch_size):
        batch_texts = rep_texts[i : i + args.batch_size]
        batch_themes = rep_themes[i : i + args.batch_size]
        batch_groups = rep_groups[i : i + args.batch_size]
        batch_labels = rep_labels[i : i + args.batch_size]

        print(f"LLM {i}-{i + len(batch_texts)} / {len(rep_texts)}")
        results = analyze_batch(
            batch_texts, batch_themes, batch_groups, tokenizer, model, compact=compact_llm
        )

        for label, result in zip(batch_labels, results):
            cluster_results[label] = result

    llm_elapsed = time.time() - llm_start
    print(f"LLM: {llm_elapsed:.1f}с ({len(rep_texts)/llm_elapsed:.2f} представит./с)")

    rep_set = set(representatives.values())
    cluster_sizes = pd.Series(labels).value_counts().to_dict()

    problems, severities, summaries = [], [], []
    for i, label in enumerate(labels):
        p, s, sm_llm = cluster_results[label]
        p = refine_problem(p, texts[i], themes_list[i], groups_list[i])
        row = df.iloc[i]
        s = refine_severity(
            s, texts[i], themes_list[i], groups_list[i], is_problem=p,
        )
        rule_summary = make_summary_from_row(row, texts[i], p)
        if summary_source == "theme":
            sm = rule_summary
        elif summary_source == "llm":
            sm = merge_llm_summary(rule_summary, sm_llm)
        elif cluster_sizes.get(label, 1) == 1 or i in rep_set:
            sm = merge_llm_summary(rule_summary, sm_llm)
        else:
            sm = rule_summary
        problems.append(p)
        severities.append(s)
        summaries.append(sm)

    df[COL_PROBLEM] = problems
    df[COL_SEVERITY] = severities
    df[COL_SUMMARY] = summaries

    total = time.time() - t0
    print(f"Итого: {total:.1f}с, сжатие {n}/{len(rep_indices)} = {n/len(rep_indices):.0f}x")

    return df


def main():
    args = parse_args()
    df = run_cluster_analysis(args)

    output = args.output or f"result_cluster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    select_columns(attach_severity_labels(df), RESULT_COLUMNS).to_excel(output, index=False)

    problems = df[COL_PROBLEM].eq(True).sum()
    print(f"Сохранено: {output}")
    print(f"Проблем: {problems} ({problems/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
