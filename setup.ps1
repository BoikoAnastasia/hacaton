# Create .venv in gorodok (run from gorodok folder)
$ErrorActionPreference = "Stop"
$Project = $PSScriptRoot
$Venv = Join-Path $Project ".venv"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found in PATH. Install Python 3.11+ from python.org"
}

if (-not (Test-Path $Venv)) {
    Write-Host "Creating .venv ..."
    python -m venv $Venv
}

$Py = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"

Write-Host "Upgrading pip ..."
& $Py -m pip install --upgrade pip

Write-Host "Installing PyTorch (CUDA 13.0) ..."
& $Pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130

Write-Host "Installing project dependencies ..."
& $Pip install -r (Join-Path $Project "requirements.txt")

Write-Host ""
Write-Host "Done. Venv: $Venv"
Write-Host "Model:  .\.venv\Scripts\python.exe tools\download_model.py"
Write-Host "Run:    .\run.ps1"
