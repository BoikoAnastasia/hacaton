# ГородОК — запуск дашборда Streamlit
$ErrorActionPreference = "Stop"
$Project = $PSScriptRoot

$VenvCandidates = @(
    (Join-Path $Project ".venv"),
    (Join-Path $Project "qwen_env"),
    (Join-Path (Split-Path $Project -Parent) "qwen_env")
)

$Venv = $VenvCandidates | Where-Object {
    Test-Path (Join-Path $_ "Scripts\streamlit.exe")
} | Select-Object -First 1

if (-not $Venv) {
    Write-Host "Виртуальное окружение не найдено." -ForegroundColor Red
    Write-Host "Выполните:  .\setup.ps1" -ForegroundColor Yellow
    Write-Host "Ищем: .venv, qwen_env (в проекте или у родительской папки)"
    exit 1
}

Write-Host "ГородОК — дашборд ($([IO.Path]::GetFileName($Venv)))" -ForegroundColor Cyan

Set-Location (Join-Path $Project "dashboard")
$env:PYTHONIOENCODING = "utf-8:replace"
& "$Venv\Scripts\streamlit.exe" run app.py --server.maxUploadSize 2048
