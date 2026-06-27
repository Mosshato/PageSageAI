# ============================================================
#  PageSage AI — Load Test Runner
#  Utilizare: .\api\tests\load\run_load_test.ps1
#
#  Generează automat:
#    api/tests/load/reports/load_report_<timestamp>.md   ← pentru teză
#    api/tests/load/reports/load_report_<timestamp>.html ← cu grafice
#    api/tests/load/reports/load_stats_<timestamp>.csv   ← date brute
# ============================================================

$ErrorActionPreference = 'Stop'
$Tag = (Get-Date -Format 'yyyyMMdd_HHmmss')
$ReportsDir = Join-Path $PSScriptRoot 'reports'
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory $ReportsDir | Out-Null }

$HtmlReport = Join-Path $ReportsDir "load_report_$Tag.html"
$CsvPrefix  = Join-Path $ReportsDir "load_stats_$Tag"
$LogFile    = Join-Path $ReportsDir "load_console_$Tag.txt"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PAGESAGE AI — LOAD TEST" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Utilizatori : 20 (6 profesori + 14 studenti)" -ForegroundColor White
Write-Host "  Ramp-up     : 2 utilizatori/secunda" -ForegroundColor White
Write-Host "  Durata      : 60 secunde" -ForegroundColor White
Write-Host "  Server      : http://localhost:8000" -ForegroundColor White
Write-Host "  Raport HTML : $HtmlReport" -ForegroundColor Yellow
Write-Host "  Raport MD   : (generat automat de locustfile)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Asigura-te ca serverul Django ruleaza:" -ForegroundColor Green
Write-Host "    python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "  Pornire in 3 secunde..." -ForegroundColor Green
Start-Sleep -Seconds 3

# Rulam locust headless si salvam output-ul
$locustArgs = @(
    '-f', (Join-Path $PSScriptRoot 'locustfile.py'),
    '--host', 'http://localhost:8000',
    '--headless',
    '-u', '20',
    '-r', '2',
    '--run-time', '60s',
    '--html', $HtmlReport,
    '--csv', $CsvPrefix,
    '--only-summary'
)

Write-Host "  Rulare locust..." -ForegroundColor Cyan
& python -m locust @locustArgs 2>&1 | Tee-Object -FilePath $LogFile

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FISIERE GENERATE:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Get-ChildItem $ReportsDir -Filter "*$Tag*" | ForEach-Object {
    Write-Host "  $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Deschide raportul HTML:" -ForegroundColor Green
Write-Host "    Start-Process '$HtmlReport'" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
