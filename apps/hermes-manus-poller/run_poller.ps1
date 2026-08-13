# Scheduled entry point for the Hermes->Manus operator-task poller.
#
# Registered as a Windows Scheduled Task ("ContexiaHermesManusPoller", see
# register_poller_task.ps1) with a 1-minute repeating trigger.
#
# Unlike run_bridge.ps1 (which supervises a long-running uvicorn server and therefore needs an
# idempotent port self-check), this poller is ONE-SHOT by design: each tick does its work and
# exits. There is nothing to keep alive, so there is no liveness probe here. Overlap is prevented
# by the task's MultipleInstances=IgnoreNew setting, and the backend rejects a second claim on an
# already-dispatched task anyway.

Set-Location -Path $PSScriptRoot

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# One log file per day (not per run): a per-run file would create ~1,440 files/day.
$logFile = Join-Path $logDir ("poller-" + (Get-Date -Format "yyyyMMdd") + ".log")

# Absolute path, not the bare "python" command: Task Scheduler's environment does not necessarily
# resolve PATH the way an interactive shell does, and a PATH failure would fail silently.
$pythonExe = "C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe"

& $pythonExe main.py *>> $logFile
exit $LASTEXITCODE
