# ============================================================
#  PageSage AI — Unit + Performance Test Runner
#  Utilizare: .\load_tests\run_unit_tests.ps1
#
#  Ruleaza cele 78 de teste Django (6 module, 100 repetitii per
#  endpoint pentru performance tests) si salveaza output-ul intr-un
#  raport text cu timestamp pentru teza de licenta.
#
#  Generează:
#    load_tests/reports/unit_report_<timestamp>.txt  ← pentru teză
# ============================================================

$ErrorActionPreference = 'Stop'
$Tag = (Get-Date -Format 'yyyyMMdd_HHmmss')
$ReportsDir = Join-Path $PSScriptRoot 'reports'
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory $ReportsDir | Out-Null }

$ReportFile = Join-Path $ReportsDir "unit_report_$Tag.txt"

$Header = @"
============================================================
  PAGESAGE AI — API TESTING REPORT
  Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  Repetitii per endpoint (performance): 100
  Modul acoperite: 6 (Auth, Classroom, PDF, RAG, Animation, Quiz)
============================================================

"@

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PAGESAGE AI — UNIT + PERFORMANCE TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Module : 6 (Auth, Classroom, PDF, RAG, Animation, Quiz)" -ForegroundColor White
Write-Host "  Repeat : 100 iteratii per endpoint (performance)" -ForegroundColor White
Write-Host "  Output : $ReportFile" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Scriem header-ul in fisier
$Header | Out-File -FilePath $ReportFile -Encoding utf8

# Rulam testele si salvam output-ul simultan in consolă + fișier
Write-Host "  Rulare teste..." -ForegroundColor Cyan
Write-Host ""

python manage.py test api -v 2 2>&1 | Tee-Object -FilePath $ReportFile -Append

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RAPORT SALVAT: $ReportFile" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Cauta liniile [PERF] pentru metricile de performanta." -ForegroundColor Green
Write-Host "  Exemplu de filtrare:" -ForegroundColor White
Write-Host "    Select-String '[PERF]' '$ReportFile'" -ForegroundColor White
Write-Host ""
