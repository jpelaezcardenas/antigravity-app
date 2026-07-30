# Registers the Chatwoot<->Contexia bridge as a Windows Scheduled Task with a
# watchdog policy (whatsapp-durable-inbox). Run once, as the user who will be logged in
# when the bridge should be running (this node's founder). Re-run after editing
# run_bridge.ps1 or moving the repo — Register-ScheduledTask overwrites an existing task
# of the same name.
#
# What this buys: the bridge is currently a manually-started process — if it crashes or
# the machine reboots, WhatsApp goes dark until someone notices and restarts it by hand.
#
# Uses a 1-minute repeating trigger + an idempotent self-check inside run_bridge.ps1
# (exits immediately if the bridge already answers on :8090), NOT Settings'
# RestartOnFailure/RestartCount/RestartInterval — that was tested live (kill the process,
# wait past its own 1-minute interval) and Windows never re-launched the action; the task
# just sat in the "Ready" state. That is a known, long-reported Task Scheduler limitation,
# not a misconfiguration here. A plain repeating trigger has no such dependency on Windows
# correctly detecting "failure" — each tick either finds the bridge healthy (no-op, thanks
# to MultipleInstancesPolicy=IgnoreNew and the self-check) or finds it dead and starts it.
#
# Deliberately triggers "AtLogOn" for the current interactive session, not "run whether
# user is logged on or not" — the latter requires storing a Windows account password in
# the task, which this script will not do. This matches the sovereign-local-node model
# already in place for Chatwoot/Docker Desktop: the bridge runs while this laptop is on
# and logged in, not as a headless server.

$ErrorActionPreference = "Stop"

$taskName = "ContexiaChatwootBridge"
$scriptPath = Join-Path $PSScriptRoot "run_bridge.ps1"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn

# "Once, now, then repeat every 1 minute, forever" — the watchdog tick. RepetitionDuration
# must be finite for New-ScheduledTaskTrigger, so this uses the longest practical span
# (roughly 10 years) rather than an unsupported "infinite" value; re-run this script before
# then, or extend it.
$watchdogTrigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger @($logonTrigger, $watchdogTrigger) `
    -Settings $settings `
    -Description "Chatwoot<->Contexia WhatsApp bridge (whatsapp-durable-inbox). Watchdog re-checks every minute and restarts if down; logs to apps/chatwoot-bridge/logs/." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host "It will start at your next log on. To start it immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To check status:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "To stop and unregister:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
