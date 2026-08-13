# Registers the Hermes->Manus poller as a Windows Scheduled Task.
# Run once, as the user who will be logged in when the poller should run (this node's founder).
# Re-run after editing run_poller.ps1 or moving the repo — Register-ScheduledTask overwrites an
# existing task of the same name.
#
# Cadence: every minute, one-shot each time (see run_poller.ps1). A minute is plenty — campaign
# dispatch is not latency-sensitive, and Manus tasks take minutes-to-hours to finish anyway.
#
# Mirrors register_bridge_task.ps1's proven setup, minus the crash-recovery machinery the bridge
# needs: a one-shot script has nothing to restart. MultipleInstances=IgnoreNew is what prevents a
# slow tick from overlapping the next one.
#
# Deliberately triggers "AtLogOn" for the current interactive session, NOT "run whether user is
# logged on or not" — the latter requires storing a Windows account password in the task, which
# this script will not do. Matches the sovereign-local-node model already used for
# Chatwoot/Docker Desktop and the Chatwoot bridge.

$ErrorActionPreference = "Stop"

$taskName = "ContexiaHermesManusPoller"
$scriptPath = Join-Path $PSScriptRoot "run_poller.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

# "Once, now, then repeat every 1 minute". RepetitionDuration must be finite for
# New-ScheduledTaskTrigger, so this uses the longest practical span (~10 years).
$tickTrigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
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
    -Description "Hermes->Manus operator-task poller (hermes-manus-poller-activation). One-shot every minute: claims approved operator_tasks, dispatches them to the Manus API, reports results back. Logs to apps/hermes-manus-poller/logs/." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host ""
Write-Host "IMPORTANT: the poller stays inert until MANUS_API_KEY is set in"
Write-Host "  apps\hermes-manus-poller\.env"
Write-Host ""
Write-Host "Start it immediately:   Start-ScheduledTask -TaskName '$taskName'"
Write-Host "Check status:           Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "Unregister:             Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
