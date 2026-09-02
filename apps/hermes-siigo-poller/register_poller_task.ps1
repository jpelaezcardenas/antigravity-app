# Registers the Hermes->Siigo sync poller as a Windows Scheduled Task.
# Run once, as the user who will be logged in when the poller should run.
#
# Cadence: nightly at 2 AM. Siigo data is day-old by design (the API returns
# journal entries from the previous day), so sub-daily sync adds no value.
#
# Mirrors apps/hermes-hubspot-poller/register_poller_task.ps1.
# "AtLogOn" trigger: runs only while the user is logged in (sovereign local node — no
# stored Windows credential, consistent with Hermes / chatwoot-bridge / manus-poller).

$ErrorActionPreference = "Stop"

$taskName  = "ContexiaHermesSiigoPoller"
$scriptDir = $PSScriptRoot
$mainPy    = Join-Path $scriptDir "main.py"

# Use pythonw.exe (no console window) if available; fall back to python.exe.
$pythonExe = (Get-Command "pythonw.exe" -ErrorAction SilentlyContinue)?.Source
if (-not $pythonExe) { $pythonExe = (Get-Command "python.exe").Source }

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$mainPy`"" `
    -WorkingDirectory $scriptDir

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

# Nightly at 02:00
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger @($logonTrigger, $dailyTrigger) `
    -Settings $settings `
    -Description "Hermes->Siigo sync poller (real-data-ingestion-mvp). Nightly at 2 AM: pulls Siigo journals+invoices for configured tenants and ingests into Shadow GL via POST /internal/siigo-sync/run." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host ""
Write-Host "REQUIRED: set these in apps\hermes-siigo-poller\.env before running:"
Write-Host "  INTERNAL_API_KEY=<same value as Railway INTERNAL_API_KEY env var>"
Write-Host "  SIIGO_ELIGIBLE_TENANTS=<uuid1>,<uuid2>  # tenants that have SIIGO_* creds in Railway"
Write-Host ""
Write-Host "Test with dry-run:   python `"$mainPy`" --dry-run"
Write-Host "Start now:           Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Check status:        Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "Unregister:          Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
