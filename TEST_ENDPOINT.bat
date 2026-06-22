@echo off
echo Testing https://contexia.online/api/v1/secrets/health
echo.
curl -s https://contexia.online/api/v1/secrets/health
echo.
echo.
echo Done. If "Not Found" -> deploy still building, wait 1 min and rerun.
echo If "unhealthy" -> endpoint LIVE (bw CLI / env vars pending = next step).
pause
