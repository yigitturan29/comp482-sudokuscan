$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ must be installed.' }
}
& '.venv\Scripts\python.exe' -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& '.venv\Scripts\python.exe' -c "from sudokuscan.recognition import find_tesseract; print('Tesseract:', find_tesseract())"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Install Tesseract 5 + English data using the README instructions, then run this again.'
    exit 1
}
Write-Host 'Ready. Run: .\demo.ps1'
