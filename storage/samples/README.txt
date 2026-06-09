Сюда положите тестовый Excel для локального запуска пайплайна.

Файлы .xlsx в эту папку не попадают в Git (могут быть большими).
После клонирования репозитория скопируйте свой файл, например:
  storage/samples/тестовый файл.xlsx

Команда анализа:
  .venv\Scripts\python.exe analyze\pipeline.py --input "storage\samples\ВАШ_ФАЙЛ.xlsx" --work-dir . --mode cluster --turbo
