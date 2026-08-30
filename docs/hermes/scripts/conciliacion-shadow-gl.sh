#!/usr/bin/env bash
# Contexia — Conciliación Shadow GL (3:00 AM COT / 08:00 UTC)
# Checks for discrepancies between declared and real financials
# Output: discrepancy report if issues found, SILENT if all clean (watchdog pattern)
set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app/api/v1"
TIMEOUT=20

ALERTAS=$(curl -s --max-time "$TIMEOUT" "${BACKEND}/agents/centinela-fiscal/alerts" 2>/dev/null || echo "")

if [ -z "$ALERTAS" ] || [ "$ALERTAS" = '{"detail":"Not Found"}' ]; then
  ALERTAS=$(curl -s --max-time "$TIMEOUT" "${BACKEND}/centinela/alerts" 2>/dev/null || echo "")
fi

if [ -z "$ALERTAS" ] || [ "$ALERTAS" = '{"detail":"Not Found"}' ]; then
  exit 0
fi

if command -v jq &>/dev/null; then
  COUNT=$(echo "$ALERTAS" | jq 'if type == "array" then length elif .alerts then (.alerts | length) elif .discrepancies then (.discrepancies | length) else 0 end' 2>/dev/null || echo "0")

  if [ "$COUNT" = "0" ] || [ "$COUNT" = "null" ]; then
    exit 0
  fi

  echo "CONCILIACION SHADOW GL — $(date +"%Y-%m-%d %H:%M") (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "${COUNT} discrepancia(s) detectada(s):"
  echo ""
  echo "$ALERTAS" | jq -r '
    if type == "array" then .[]
    elif .alerts then .alerts[]
    elif .discrepancies then .discrepancies[]
    else empty
    end |
    "• Tipo: \(.tipo // .type // "N/D") | Monto: \(.monto // .amount // "N/D") | Estado: \(.estado // .status // "N/D")"
  ' 2>/dev/null || echo "$ALERTAS"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Requiere revision HITL — Centinela Fiscal"
else
  echo "$ALERTAS"
fi
