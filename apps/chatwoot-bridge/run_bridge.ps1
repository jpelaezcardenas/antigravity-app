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

# ── Hide console window immediately (no flash) ──────────────────────────
# When Task Scheduler launches powershell.exe without -WindowStyle Hidden,
# a console window briefly appears. This P/Invoke hides it on the spot.
Add-Type -Name Win32 -Namespace '' -MemberDefinition @'
  [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
  [DllImport("user32.dll")]   public static extern bool ShowWindow(IntPtr h, int n);
'@ -ErrorAction SilentlyContinue
$consoleHwnd = [Win32]::GetConsoleWindow()
if ($consoleHwnd -ne [IntPtr]::Zero) { [Win32]::ShowWindow($consoleHwnd, 0) | Out-Null }  # 0 = SW_HIDE

# Idempotent self-check, not Task Scheduler's RestartOnFailure: that setting was tested live
# (kill the process, wait past its 1-minute RestartInterval) and Windows never re-launched the
# action — the task just sat in the "Ready" state. This is a known, long-reported Task Scheduler
# limitation, not a misconfiguration here. The reliable native-Windows pattern instead is a
# trigger that repeats every minute forever (see register_bridge_task.ps1) combined with this
# script exiting immediately, doing nothing, whenever the bridge is already up — so a healthy
# tick is a no-op and a dead one actually restarts it.
#
# NOTE: Test-NetConnection was replaced with TcpClient because Test-NetConnection creates a
# visible console window every minute. TcpClient is fully silent and faster.
$alreadyRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect('127.0.0.1', 8090)
    $alreadyRunning = $tcp.Connected
    $tcp.Close()
} catch { $alreadyRunning = $false }
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
