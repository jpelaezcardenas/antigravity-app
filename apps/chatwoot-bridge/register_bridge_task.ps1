# Registers the Chatwoot<->Contexia bridge as a Windows Scheduled Task with a
# restart-on-failure policy (whatsapp-durable-inbox). Run once, as the user who will be
# logged in when the bridge should be running (this node's founder). Re-run after editing
# run_bridge.ps1 or moving the repo — Register-ScheduledTask overwrites an existing task
# of the same name.
#
# What this buys: the bridge is currently a manually-started process — if it crashes or
# the machine reboots, WhatsApp goes dark until someone notices and restarts it by hand.
# A scheduled task with RestartCount/RestartInterval is the closest native-Windows
# equivalent to systemd's Restart=always (the gbrain-autopilot.service precedent).
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

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Chatwoot<->Contexia WhatsApp bridge (whatsapp-durable-inbox). Restarts automatically on crash; logs to apps/chatwoot-bridge/logs/." `
    -Force

Write-Host "Registered scheduled task '$taskName'."
Write-Host "It will start at your next log on. To start it immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To check status:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host "To stop and unregister:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
