# ============================================================
#  PageSage AI — Security Test Runner
#  Utilizare: .\api\tests\security\run_security_tests.ps1
#
#  Ruleaza cele 23 de teste de securitate Django si salveaza
#  rezultatele intr-un raport text + rezumat JSON cu timestamp.
#
#  Genereaza:
#    api/tests/security/reports/security_report_<ts>.txt   <- raport complet
#    api/tests/security/reports/security_summary_<ts>.json <- rezumat structurat
# ============================================================

$Tag        = (Get-Date -Format 'yyyyMMdd_HHmmss')
$ReportsDir = Join-Path $PSScriptRoot 'reports'
if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory $ReportsDir | Out-Null }

$ReportFile  = Join-Path $ReportsDir "security_report_$Tag.txt"
$SummaryFile = Join-Path $ReportsDir "security_summary_$Tag.json"

# ── Header ────────────────────────────────────────────────────────────────────
$Header = @"
============================================================
  PAGESAGE AI -- SECURITY TEST REPORT
  Data      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  Proprietati testate:
    SEC-1  Endpoint-uri protejate cer token valid (401 fara token)
    SEC-2  Token-uri invalide / malformate sunt respinse (401)
    SEC-3  Izolare prin ownership (teacher/student vad doar resursele lor)
    SEC-4  Separare roluri (student nu poate apela rute de teacher)
    SEC-5  Parole stocate ca hash PBKDF2, nu plaintext
============================================================

"@

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PAGESAGE AI -- SECURITY TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Output : $ReportFile" -ForegroundColor Yellow
Write-Host "  JSON   : $SummaryFile" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$Header | Out-File -FilePath $ReportFile -Encoding utf8

# ── Rulare teste ──────────────────────────────────────────────────────────────
Write-Host "  Rulare teste de securitate..." -ForegroundColor Cyan
Write-Host ""

$RawOutput = python manage.py test api.tests.security -v 2 2>&1
$RawOutput | Tee-Object -FilePath $ReportFile -Append

# ── Determinare rezultat global ───────────────────────────────────────────────
$OutputText = $RawOutput -join "`n"
$GlobalOk   = $OutputText -match '\bOK\b' -and $OutputText -notmatch 'FAILED'

# ── Extrage liniile SEC-* si construieste JSON ────────────────────────────────
$Results = @()

$SecLines = $RawOutput | Where-Object { $_ -match '\[SEC-\d+[a-z]?\]' }
foreach ($line in $SecLines) {
    if ($line -match '\[(SEC-\d+[a-z]?)\]\s+(PASS|FAIL)\s*-?\s*(.+)') {
        $Results += [ordered]@{
            id      = $Matches[1]
            status  = $Matches[2]
            detail  = $Matches[3].Trim()
        }
    }
}

# Extrage nr. total de teste si durata din linia "Ran X tests in Ys"
$TotalTests = 0
$Duration   = ''
foreach ($line in $RawOutput) {
    if ($line -match 'Ran (\d+) tests? in ([\d.]+)s') {
        $TotalTests = [int]$Matches[1]
        $Duration   = $Matches[2] + 's'
        break
    }
}

$Summary = [ordered]@{
    generated_at  = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    total_tests   = $TotalTests
    duration      = $Duration
    global_result = if ($GlobalOk) { 'OK' } else { 'FAILED' }
    properties    = @(
        [ordered]@{ code = 'SEC-1'; name = 'Unauthenticated access blocked' }
        [ordered]@{ code = 'SEC-2'; name = 'Invalid/malformed tokens rejected' }
        [ordered]@{ code = 'SEC-3'; name = 'Ownership isolation enforced' }
        [ordered]@{ code = 'SEC-4'; name = 'Role separation enforced' }
        [ordered]@{ code = 'SEC-5'; name = 'Passwords stored as hashes' }
    )
    results       = $Results
}

$Summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $SummaryFile -Encoding utf8

# ── Footer in raportul txt ────────────────────────────────────────────────────
$Footer = @"

============================================================
  REZULTAT GLOBAL : $(if ($GlobalOk) { 'OK - toate testele au trecut' } else { 'FAILED' })
  Total teste      : $TotalTests
  Durata           : $Duration
  Raport complet   : $ReportFile
  Rezumat JSON     : $SummaryFile
============================================================
"@

$Footer | Out-File -FilePath $ReportFile -Encoding utf8 -Append

# ── Output final in consola ───────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($GlobalOk) {
    Write-Host "  REZULTAT: OK - toate testele au trecut" -ForegroundColor Green
} else {
    Write-Host "  REZULTAT: FAILED" -ForegroundColor Red
}
Write-Host "  Total teste : $TotalTests  |  Durata: $Duration" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Raport complet : $ReportFile" -ForegroundColor Yellow
Write-Host "  Rezumat JSON   : $SummaryFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Filtrare rapida rezultate SEC-*:" -ForegroundColor White
Write-Host "    Select-String 'SEC-' '$ReportFile'" -ForegroundColor Gray
Write-Host ""
