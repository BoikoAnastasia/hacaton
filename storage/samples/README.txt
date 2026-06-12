Тестовые Excel для локального запуска
=====================================

Положите сюда файл .xlsx с обращениями граждан.

Файлы .xlsx в Git не коммитятся (могут быть очень большими).

Пример имени:
  storage/samples/обращения_омск.xlsx

Запуск дашборда
---------------
  run.bat
  или:  run.ps1

Обработка из командной строки (рекомендуемый режим)
---------------------------------------------------
  .venv\Scripts\python.exe analyze\pipeline.py ^
    --input "storage\samples\ВАШ_ФАЙЛ.xlsx" ^
    --work-dir . ^
    --mode cluster --turbo

Быстрый тест без GPU
--------------------
  .venv\Scripts\python.exe analyze\pipeline.py ^
    --input "storage\samples\ВАШ_ФАЙЛ.xlsx" ^
    --work-dir . ^
    --mode fast ^
    --limit 500

Результаты появятся в:
  storage\output\Отчет от дд.мм.гг - чч.мм\

Подробнее: README.md и docs\РЕЖИМЫ_ОБРАБОТКИ.md
