# Gorodok dashboard launcher
$Project = $PSScriptRoot
$Venv = @(
    (Join-Path $Project ".venv"),
    (Join-Path (Split-Path $Project -Parent) "qwen_env")
) | Where-Object { Test-Path (Join-Path $_ "Scripts\streamlit.exe") } | Select-Object -First 1

if (-not $Venv) {
    Write-Error "Venv not found. Run: .\setup.ps1"
}

Set-Location (Join-Path $Project "dashboard")
$env:PYTHONIOENCODING = "utf-8:replace"
& "$Venv\Scripts\streamlit.exe" run app.py --server.maxUploadSize 2048
