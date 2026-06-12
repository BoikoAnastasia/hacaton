# ГородОК — установка окружения (.venv + зависимости)
$ErrorActionPreference = "Stop"
$Project = $PSScriptRoot
$Venv = Join-Path $Project ".venv"

Write-Host "ГородОК — установка" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python не найден в PATH. Установите Python 3.11+ с python.org"
}

$pyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python: $pyVersion"

if (-not (Test-Path $Venv)) {
    Write-Host "Создаю .venv ..."
    python -m venv $Venv
}

$Py = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"

Write-Host "Обновляю pip ..."
& $Py -m pip install --upgrade pip

Write-Host "Устанавливаю PyTorch (CUDA 13.0) ..."
Write-Host "  (для CPU-only замените на: pip install torch torchvision)"
& $Pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130

Write-Host "Устанавливаю зависимости проекта ..."
& $Pip install -r (Join-Path $Project "requirements.txt")

Write-Host ""
Write-Host "Готово." -ForegroundColor Green
Write-Host "  Окружение:  $Venv"
Write-Host "  Модель:     .\.venv\Scripts\python.exe tools\download_model.py"
Write-Host "  Дашборд:    .\run.ps1"
Write-Host "  Документация: README.md, docs\"
Write-Host ""
