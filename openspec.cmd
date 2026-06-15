@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
"C:\Users\contexia\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" "%SCRIPT_DIR%tools\openspec-cli.mjs" %*
