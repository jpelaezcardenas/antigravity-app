#!/usr/bin/env bash
# Contexia — Auditoria Sombra nocturna (2:00 AM COT / 07:00 UTC)
# Shadow GL: reconciliacion tecnica nocturna, deteccion de discrepancias DIAN
# Watchdog pattern: silencio si clean, reporte si hay discrepancias
set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app/api/v1"
COMPANY_ID="ff1a8b7c-b0a1-422e-bc48-fac6242be027"
TIMEOUT=30

CURL_AUTH=()
if [ -n "${HERMES_BRIDGE_TOKEN:-}" ]; then
  CURL_AUTH=(-H "Authorization: Bearer ${HERMES_BRIDGE_TOKEN}")
fi

RESULTADO=$(curl -s --max-time "$TIMEOUT" \
  -X POST \
  -H "Content-Type: application/json" \
  "${CURL_AUTH[@]}" \
  -d "{\"company_id\": \"${COMPANY_ID}\", \"mode\": \"nightly\"}" \
  "${BACKEND}/wizard/auditoria-sombra" 2>/dev/null || echo "")

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  RESULTADO=$(curl -s --max-time "$TIMEOUT" \
    "${CURL_AUTH[@]}" \
    "${BACKEND}/agents/auditoria-sombra/run" 2>/dev/null || echo "")
fi

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  exit 0
fi

if command -v jq &>/dev/null; then
  STATUS=$(echo "$RESULTADO" | jq -r '.status // .estado // "unknown"' 2>/dev/null || echo "unknown")
  DISCREPANCIAS=$(echo "$RESULTADO" | jq '
    (.discrepancias // .discrepancies // []) | length
  ' 2>/dev/null || echo "0")

  if [ "$STATUS" = "clean" ] || [ "$STATUS" = "ok" ] || [ "$DISCREPANCIAS" = "0" ]; then
    exit 0
  fi

  echo "AUDITORIA SOMBRA — $(date +"%Y-%m-%d %H:%M") (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Estado Shadow GL: ${STATUS}"
  echo "Discrepancias encontradas: ${DISCREPANCIAS}"
  echo ""
  echo "$RESULTADO" | jq -r '
    (.discrepancias // .discrepancies // []) | .[] |
    "• Cuenta: \(.cuenta // .account // "N/D") | Diferencia: \(.diferencia // .difference // "N/D") COP | Tipo: \(.tipo // .type // "N/D")"
  ' 2>/dev/null || echo "$RESULTADO"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Auditoria Sombra — Requiere revision antes de apertura"
else
  echo "$RESULTADO"
fi
