# Supervised entry point for the Chatwoot<->Contexia bridge (whatsapp-durable-inbox).
#
# Registered as a Windows Scheduled Task ("ContexiaChatwootBridge", see
# register_bridge_task.ps1) with a restart-on-failure policy — the closest native-Windows
# equivalent to systemd's Restart=always, matching the gbrain-autopilot.service precedent
# noted in the architecture plan. If uvicorn crashes, Task Scheduler restarts this script.
#
# Not meant to be run manually except for a one-off foreground check — use the scheduled task
# for anything left running unattended, so a crash gets noticed and restarted automatically.

Set-Location -Path $PSScriptRoot

# Idempotent self-check, not Task Scheduler's RestartOnFailure: that setting was tested live
# (kill the process, wait past its 1-minute RestartInterval) and Windows never re-launched the
# action — the task just sat in the "Ready" state. This is a known, long-reported Task Scheduler
# limitation, not a misconfiguration here. The reliable native-Windows pattern instead is a
# trigger that repeats every minute forever (see register_bridge_task.ps1) combined with this
# script exiting immediately, doing nothing, whenever the bridge is already up — so a healthy
# tick is a no-op and a dead one actually restarts it.
$alreadyRunning = Test-NetConnection -ComputerName "127.0.0.1" -Port 8090 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($alreadyRunning) {
    exit 0
}

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "bridge-$timestamp.log"

# Absolute path, not the bare "python" command: Task Scheduler's environment does not
# necessarily resolve PATH the same way an interactive shell does, and a PATH-resolution
# failure here would otherwise fail silently with an empty log.
$pythonExe = "C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe"

& $pythonExe -m uvicorn main:app --host 0.0.0.0 --port 8090 *>> $logFile
exit $LASTEXITCODE
