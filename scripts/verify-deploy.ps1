# Post-deploy route check for contexia.online. Retries for a couple minutes since
# Vercel's edge network doesn't always propagate a fresh deploy to every region
# instantly (seen live 2026-09-17: a route 404'd for ~90s after "READY").
#
# Usage:
#   pwsh scripts/verify-deploy.ps1 -Routes /app/patrimonio-v2,/app/fiscal-v2
#   pwsh scripts/verify-deploy.ps1                      # default smoke set

param(
    [string[]]$Routes = @(
        "/",
        "/app/bunker",
        "/app/overview", "/app/fiscal", "/app/radar", "/app/patrimonio", "/app/config",
        "/app/overview-v2", "/app/fiscal-v2", "/app/radar-v2", "/app/patrimonio-v2",
        "/app/acerca-v2", "/flujo-detalle-v2"
    ),
    [string]$BaseUrl = "https://contexia.online",
    [int]$MaxAttempts = 12,
    [int]$DelaySeconds = 10
)

$ErrorActionPreference = "Stop"
$failed = @()

foreach ($route in $Routes) {
    $url = "$BaseUrl$route"
    $ok = $false
    $lastCode = $null
    for ($i = 0; $i -lt $MaxAttempts; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $url -Method Get -MaximumRedirection 0 -UseBasicParsing -ErrorAction Stop
            $lastCode = $resp.StatusCode
        } catch {
            if ($_.Exception.Response) {
                $lastCode = [int]$_.Exception.Response.StatusCode
            } else {
                $lastCode = "ERR"
            }
        }
        if ($lastCode -eq 200 -or $lastCode -eq 307 -or $lastCode -eq 308) { $ok = $true; break }
        Start-Sleep -Seconds $DelaySeconds
    }
    if ($ok) {
        Write-Host "OK   $lastCode  $url" -ForegroundColor Green
    } else {
        Write-Host "FAIL $lastCode  $url  (after $MaxAttempts attempts, $($MaxAttempts * $DelaySeconds)s)" -ForegroundColor Red
        $failed += $url
    }
}

Write-Host ""
if ($failed.Count -gt 0) {
    Write-Host "FAILED ROUTES:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
} else {
    Write-Host "All $($Routes.Count) routes OK." -ForegroundColor Green
}
