# Supervised entry point for the Chatwoot<->Contexia bridge (whatsapp-durable-inbox).
#
# Registered as a Windows Scheduled Task ("ContexiaChatwootBridge", see
# register_bridge_task.ps1) with a restart-on-failure policy — the closest native-Windows
# equivalent to systemd's Restart=always, matching the gbrain-autopilot.service precedent
# noted in the architecture plan. If uvicorn crashes, Task Scheduler restarts this script.
#
# Not meant to be run manually except for a one-off foreground check — use the scheduled task
# for anything left running unattended, so a crash gets noticed and restarted automatically.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "bridge-$timestamp.log"

python -m uvicorn main:app --host 0.0.0.0 --port 8090 *>> $logFile
