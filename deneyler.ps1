param(
    [string]$VeriDizini = 'data\received_20261109_zip',
    [string]$OgrenciNo = 'STUDENT NUMBER'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    & (Join-Path $PSScriptRoot 'kurulum.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. See README.md.' }
}
$taskImages = Join-Path $VeriDizini 'images'
$taskAnnotations = Join-Path $VeriDizini 'annotations'
if (-not (Test-Path -LiteralPath $taskImages -PathType Container)) {
    throw 'Extract the private data package alongside the code before running experiments.'
}
function Invoke-Experiment {
    param([string[]]$TaskArguments)
    & $taskPython @TaskArguments
    if ($LASTEXITCODE -ne 0) { throw "Experiment failed: $($TaskArguments[0])" }
}
Invoke-Experiment -TaskArguments @('sudoku_scan.py','--batch',$taskImages,'--outdir','results/zip_automatic')
Invoke-Experiment -TaskArguments @('tools/evaluate.py','--annotations',$taskAnnotations,'--results','results/zip_automatic','--output','results/zip_automatic_metrics.json')
Invoke-Experiment -TaskArguments @('tools/compare_models.py','--annotations',$taskAnnotations,'--results','results/zip_automatic','--outdir','results/model_comparison')
Invoke-Experiment -TaskArguments @('tools/preview_annotations.py','--images',$taskImages,'--annotations',$taskAnnotations,'--outdir','results/zip_annotation_preview')
Invoke-Experiment -TaskArguments @('tools/ocr_study.py','--annotations',$taskAnnotations,'--results','results/zip_automatic','--outdir','results/zip_ocr_study')
Invoke-Experiment -TaskArguments @('tools/harris_study.py','--images',$taskImages,'--annotations',$taskAnnotations,'--upright-only','--out','results/zip_harris_study.csv')
# A metadata audit can report provenance issues independently of working code.
& $taskPython tools/check_dataset.py --images $taskImages --annotations $taskAnnotations --output results/zip_dataset_check.json
if ($LASTEXITCODE -gt 1) { throw 'Dataset audit could not execute.' }
Invoke-Experiment -TaskArguments @('tools/build_received_report.py','--student-number',$OgrenciNo,'--dataset',$VeriDizini)
Write-Host 'Completed. Report source: report\private\report.tex'
Write-Host 'See report\README.md to compile the IEEE PDF.'

