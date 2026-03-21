# Sample data distribution script
# Creates: 1 sample, 120 for build, 480 for test

$sourceDir = "f:\cv-filtering\data"
$sampleDir = "f:\cv-filtering\demo\data\sample_1"
$buildDir = "f:\cv-filtering\demo\data\build_120"
$testDir = "f:\cv-filtering\demo\data\test_480"

Write-Host "=== Starting data sampling ===" -ForegroundColor Green

# Get all categories
$categories = @()
Get-ChildItem -Path $sourceDir -Directory | ForEach-Object {
    $categories += $_.Name
}

Write-Host "Found categories: $($categories.Count)" -ForegroundColor Cyan
Write-Host $categories

# Sample 1: Just 1 random PDF from first category
Write-Host "[1/3] Sampling 1 PDF for quick test..." -ForegroundColor Yellow
$firstCategory = $categories[0]
$firstCatPath = Join-Path $sourceDir $firstCategory
$onePdf = Get-ChildItem -Path $firstCatPath -Filter "*.pdf" | Get-Random -Count 1
Copy-Item -Path $onePdf.FullName -Destination $sampleDir -Force
Write-Host "OK Sampled: $($onePdf.Name)" -ForegroundColor Green

# Sample 120: 5 from each category
Write-Host "[2/3] Sampling 120 PDFs (5 per category) for build..." -ForegroundColor Yellow
$buildCount = 0
foreach ($cat in $categories) {
    $catPath = Join-Path $sourceDir $cat
    $pdfs = Get-ChildItem -Path $catPath -Filter "*.pdf"
    $count = [Math]::Min(5, $pdfs.Count)
    $selected = $pdfs | Get-Random -Count $count
    foreach ($pdf in $selected) {
        Copy-Item -Path $pdf.FullName -Destination $buildDir -Force
        $buildCount++
    }
    Write-Host "  $cat : $count PDFs" -ForegroundColor Gray
}
Write-Host "OK Total build samples: $buildCount" -ForegroundColor Green

# Sample 480: 20 from each category
Write-Host "[3/3] Sampling 480 PDFs (20 per category) for test..." -ForegroundColor Yellow
$testCount = 0
foreach ($cat in $categories) {
    $catPath = Join-Path $sourceDir $cat
    $pdfs = Get-ChildItem -Path $catPath -Filter "*.pdf"
    $count = [Math]::Min(20, $pdfs.Count)
    $selected = $pdfs | Get-Random -Count $count
    foreach ($pdf in $selected) {
        Copy-Item -Path $pdf.FullName -Destination $testDir -Force
        $testCount++
    }
    Write-Host "  $cat : $count PDFs" -ForegroundColor Gray
}
Write-Host "OK Total test samples: $testCount" -ForegroundColor Green

Write-Host "=== Sampling Complete ===" -ForegroundColor Green
Write-Host "sample_1: $(Get-ChildItem $sampleDir -Filter *.pdf | Measure-Object | Select-Object -ExpandProperty Count)" -ForegroundColor Cyan
Write-Host "build_120: $buildCount" -ForegroundColor Cyan
Write-Host "test_480: $testCount" -ForegroundColor Cyan
