$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'First run: powershell -ExecutionPolicy Bypass -File .\kurulum.ps1'
}
& $taskPython tools/demo.py --outdir results/demo
if ($LASTEXITCODE -ne 0) { throw 'Demo failed; read the error above.' }
Write-Host 'This demo uses synthetic known corners. Use sudoku_scan.py for automatic Harris selection.'
Write-Host 'Open results\demo\known_GT_debug.png and results\demo\demo_summary.json.'
