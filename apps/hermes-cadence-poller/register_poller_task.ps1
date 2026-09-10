# Registers the Hermes follow-up-cadence poller as a Windows Scheduled Task.
# Run once, as the user who will be logged in when the poller should run.
#
# Cadence: every 60 minutes. The scripted touches themselves are day-granular (D1/D2/D4/D7/D14),
# so hourly checking is more than enough responsiveness without hammering Supabase/Railway.
#
# Mirrors apps/hermes-gmail-poller/register_poller_task.ps1 exactly (New-ScheduledTaskAction with
# -WorkingDirectory so a relative .env load resolves correctly — NOT a `cmd /c` wrapper).
# "AtLogOn" trigger: runs only while the user is logged in (sovereign local node — no stored
# Windows credential, consistent with Hermes / chatwoot-bridge / the other pollers).

$ErrorActionPreference = "Stop"

$taskName  = "ContexiaHermesCadencePoller"
$scriptDir = $PSScriptRoot
$mainPy    = Join-Path $scriptDir "main.py"

# Use pythonw.exe (no console window) if available; fall back to python.exe.
$pythonCmd = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
if ($pythonCmd) { $pythonExe = $pythonCmd.Source } else { $pythonExe = (Get-Command "python.exe").Source }

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$mainPy`"" `
    -WorkingDirectory $scriptDir

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

$tickTrigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 60) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger @($logonTrigger, $tickTrigger) `
    -Settings $settings `
    -Description "Hermes follow-up-cadence poller (taty-followup-cadence). Every 60 min: checks NUEVOS crm_leads for the next due scripted WhatsApp touch (D1/D2/D4/D7/D14) and sends it via POST /internal/cadence/send-touch." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host ""
Write-Host "REQUIRED SETUP before the poller does anything:"
Write-Host "  1. Create apps\hermes-cadence-poller\.env with:"
Write-Host "       INTERNAL_API_KEY=<same value as Railway INTERNAL_API_KEY>"
Write-Host "       SUPABASE_URL=<project url>"
Write-Host "       SUPABASE_SERVICE_ROLE_KEY=<service role key>"
Write-Host "  2. Apply migration 0051_crm_leads_cadence.sql to the live database (founder approval"
Write-Host "     required before this poller can do anything real — see the migration file header)."
Write-Host "  3. Run once interactively to sanity-check:"
Write-Host "       python `"$mainPy`" --dry-run"
Write-Host ""
Write-Host "Start now:      Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Check status:   Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "Unregister:     Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
