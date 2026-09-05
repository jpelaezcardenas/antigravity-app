# Registers the Hermes Gmail attachment ingestion poller as a Windows Scheduled Task.
# Run once, as the user who will be logged in when the poller should run.
#
# Cadence: every 15 minutes. Clients email invoices/CSVs to Taty throughout the day;
# 15 min keeps ingestion responsive without hammering the Gmail API quota.
#
# Mirrors apps/hermes-hubspot-poller/register_poller_task.ps1.
# "AtLogOn" trigger: runs only while the user is logged in (sovereign local node —
# no stored Windows credential, consistent with Hermes / chatwoot-bridge).

$ErrorActionPreference = "Stop"

$taskName  = "ContexiaHermesGmailPoller"
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
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
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
    -Description "Hermes Gmail attachment ingestion poller (real-data-ingestion-mvp). Every 15 min: reads Taty's inbox for invoice/CSV attachments, resolves tenant via gmail_sender_map, ingests via POST /internal/ingest/file." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host ""
Write-Host "REQUIRED SETUP before the poller does anything:"
Write-Host "  1. Google Cloud Console -> OAuth 2.0 Client ID (Desktop app) -> download credentials.json"
Write-Host "     into apps\hermes-gmail-poller\"
Write-Host "  2. Create apps\hermes-gmail-poller\.env with:"
Write-Host "       INTERNAL_API_KEY=<same value as Railway INTERNAL_API_KEY>"
Write-Host "       SUPABASE_URL=<project url>"
Write-Host "       SUPABASE_SERVICE_ROLE_KEY=<service role key>"
Write-Host "       GMAIL_INBOX_ADDRESS=<Taty's gmail address>"
Write-Host "  3. Run once interactively to complete the OAuth2 flow (opens a browser):"
Write-Host "       python `"$mainPy`" --dry-run"
Write-Host "  4. Populate gmail_sender_map in Supabase (sender_email -> tenant_id) per client."
Write-Host ""
Write-Host "Start now:      Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Check status:   Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "Unregister:     Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
