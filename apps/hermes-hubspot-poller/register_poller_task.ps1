# Registers the Hermes->HubSpot sync poller as a Windows Scheduled Task.
# Run once, as the user who will be logged in when the poller should run (this node's founder).
#
# Cadence: every 5 minutes, one-shot each time (see run_poller.ps1). HubSpot is a
# commercial/reporting layer, not the operational surface (design.md Goals) — a few minutes of
# lag is acceptable and keeps this well under free-tier API rate limits.
#
# Mirrors apps/hermes-manus-poller/register_poller_task.ps1. Deliberately triggers "AtLogOn" for
# the current interactive session, NOT "run whether user is logged on or not" (no stored Windows
# password) — same sovereign-local-node model as the rest of Hermes.

$ErrorActionPreference = "Stop"

$taskName = "ContexiaHermesHubspotPoller"
$scriptPath = Join-Path $PSScriptRoot "run_poller.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

$tickTrigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
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
    -Description "Hermes->HubSpot sync poller (hubspot-sync-renta-natural). One-shot every 5 minutes: syncs crm_leads -> HubSpot Contacts+Deals and b2b_clients -> HubSpot Companies. Logs to apps/hermes-hubspot-poller/logs/." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host ""
Write-Host "IMPORTANT: the poller stays inert until HUBSPOT_ACCESS_TOKEN and"
Write-Host "  SUPABASE_SERVICE_ROLE_KEY are set in apps\hermes-hubspot-poller\.env"
Write-Host ""
Write-Host "Start it immediately:   Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Check status:           Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "Unregister:             Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
