# Phase 6 Stage 10 E2E Test Helper
# Usage: powershell -File test-e2e.ps1

param(
    [ValidateSet("create-csv", "upload-csv", "check-queue", "check-persistence")]
    [string]$Action = "create-csv"
)

$BaseURL = "http://localhost:8000/api/v1/shadow-gl"
$DBQuery = "SELECT * FROM approval_queue WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1"

function Create-ImbalancedCSV {
    $csv = @"
Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,75.00
2026-06-25,TX-002,1100,Sales Receivable,150.00,
2026-06-25,TX-002,4100,Sales Revenue,,100.00
"@
    $csv | Set-Content -Path "./imbalanced.csv" -Encoding UTF8
    Write-Host "✅ Created imbalanced.csv (Debits=250, Credits=175)" -ForegroundColor Green
}

function Upload-CSV {
    if (-not (Test-Path "./imbalanced.csv")) {
        Write-Host "❌ imbalanced.csv not found. Run: powershell -File test-e2e.ps1 create-csv" -ForegroundColor Red
        return
    }

    $csv = Get-Content -Path "./imbalanced.csv" -Raw
    try {
        $response = Invoke-WebRequest -Uri "$BaseURL/siigo-csv/ingest" `
            -Method POST `
            -Body $csv `
            -ContentType "text/plain" `
            -ErrorAction SilentlyContinue

        if ($response.StatusCode -eq 200) {
            Write-Host "⚠️  CSV was accepted (not imbalanced?)" -ForegroundColor Yellow
        }
    } catch {
        if ($_.Exception.Response.StatusCode.Value__ -eq 400) {
            Write-Host "✅ Backend returned 400 (imbalance detected)" -ForegroundColor Green
            Write-Host "   Detail: $($_.ErrorDetails.Message)" -ForegroundColor Gray
        } else {
            Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

function Check-ApprovalQueue {
    Write-Host "`n📋 Checking approval_queue..." -ForegroundColor Cyan
    Write-Host "   You need to query Supabase directly:" -ForegroundColor Gray
    Write-Host "   SQL: SELECT id, status, created_at FROM approval_queue WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1;" -ForegroundColor Gray
    Write-Host "`n   Expected: 1 pending row with your CSV data" -ForegroundColor Gray
}

function Check-Persistence {
    Write-Host "`n✅ Checking erp_journal_entries..." -ForegroundColor Cyan
    Write-Host "   You need to query Supabase directly:" -ForegroundColor Gray
    Write-Host "   SQL: SELECT id, external_reference_id, status FROM erp_journal_entries WHERE external_reference_id IN ('TX-001','TX-002');" -ForegroundColor Gray
    Write-Host "`n   Expected AFTER approval: 2 rows (TX-001, TX-002)" -ForegroundColor Gray
}

switch ($Action) {
    "create-csv" { Create-ImbalancedCSV }
    "upload-csv" { Upload-CSV }
    "check-queue" { Check-ApprovalQueue }
    "check-persistence" { Check-Persistence }
    default { Create-ImbalancedCSV }
}

Write-Host "`n📍 Stage 10 E2E Test Steps:" -ForegroundColor Cyan
Write-Host "  1. Create CSV:    powershell -File test-e2e.ps1 create-csv" -ForegroundColor Gray
Write-Host "  2. Upload CSV:    powershell -File test-e2e.ps1 upload-csv" -ForegroundColor Gray
Write-Host "  3. Check queue:   powershell -File test-e2e.ps1 check-queue" -ForegroundColor Gray
Write-Host "  4. Approve in Hermes UI (localhost:3000)" -ForegroundColor Gray
Write-Host "  5. Check persist: powershell -File test-e2e.ps1 check-persistence" -ForegroundColor Gray
