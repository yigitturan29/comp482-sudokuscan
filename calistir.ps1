param(
    [string]$Girdi,
    [string]$Cikti = 'results\tarama'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    & (Join-Path $PSScriptRoot 'kurulum.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. See README.md.' }
}
if (-not $Girdi) {
    $taskDataset = Join-Path $PSScriptRoot 'data\received_20261109_zip\images'
    if (Test-Path -LiteralPath $taskDataset -PathType Container) { $Girdi = $taskDataset }
    else { $Girdi = (Read-Host 'Enter the photo or image-folder path').Trim('"') }
}
if (Test-Path -LiteralPath $Girdi -PathType Container) {
    & $taskPython sudoku_scan.py --batch $Girdi --outdir $Cikti
} elseif (Test-Path -LiteralPath $Girdi -PathType Leaf) {
    & $taskPython sudoku_scan.py --input $Girdi --outdir $Cikti
} else {
    throw "Photo or folder does not exist: $Girdi"
}
if ($LASTEXITCODE -ne 0) { throw 'Some images failed; inspect their result JSON files.' }
Write-Host "Results: $([System.IO.Path]::GetFullPath($Cikti))"
