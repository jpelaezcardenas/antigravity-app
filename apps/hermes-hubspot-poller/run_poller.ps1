# Scheduled entry point for the Hermes->HubSpot sync poller.
#
# Registered as a Windows Scheduled Task ("ContexiaHermesHubspotPoller", see
# register_poller_task.ps1) with a 5-minute repeating trigger. One-shot by design (same pattern
# as apps/hermes-manus-poller/run_poller.ps1): each tick does its work and exits.

Set-Location -Path $PSScriptRoot

Add-Type -Name Win32 -Namespace '' -MemberDefinition @'
  [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
  [DllImport("user32.dll")]   public static extern bool ShowWindow(IntPtr h, int n);
'@ -ErrorAction SilentlyContinue
$consoleHwnd = [Win32]::GetConsoleWindow()
if ($consoleHwnd -ne [IntPtr]::Zero) { [Win32]::ShowWindow($consoleHwnd, 0) | Out-Null }  # 0 = SW_HIDE

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$logFile = Join-Path $logDir ("poller-" + (Get-Date -Format "yyyyMMdd") + ".log")

$pythonExe = "C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe"

& $pythonExe main.py *>> $logFile
exit $LASTEXITCODE
