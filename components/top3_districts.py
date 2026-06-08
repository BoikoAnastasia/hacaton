def get_top3_districts(df):
  top3 = (
    df.groupby("Населенный пункт")
    .agg(
      count=("Населенный пункт", "size"),
      severity=("Серьёзность", "mean")
    )
    .sort_values("count", ascending=False)
    .head(3)
    .reset_index()
  )
  result = []

  for idx, row in top3.iterrows():

    district_df = df[
      df["Населенный пункт"] == row["Населенный пункт"]
    ]

    problems = (
      district_df["Группа тем"]
      .value_counts()
      .head(3)
      .index
      .tolist()
    )

    result.append({
      "rank": idx + 1,
      "district": row["Населенный пункт"],
      "count": int(row["count"]),
      "severity": round(row["severity"], 1),
      "problems": problems
    })

  return result