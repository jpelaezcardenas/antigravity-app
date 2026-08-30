#!/usr/bin/env bash
# Contexia — Centinela Fiscal (12:00 PM COT / 17:00 UTC, lunes-viernes)
# Mid-day compliance check: detecta discrepancias antes del cierre de jornada
# Watchdog pattern: silencio si todo OK, alerta si hay riesgo fiscal
set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app/api/v1"
COMPANY_ID="ff1a8b7c-b0a1-422e-bc48-fac6242be027"
TIMEOUT=20

CURL_AUTH=()
if [ -n "${HERMES_BRIDGE_TOKEN:-}" ]; then
  CURL_AUTH=(-H "Authorization: Bearer ${HERMES_BRIDGE_TOKEN}")
fi

RESULTADO=$(curl -s --max-time "$TIMEOUT" \
  -H "Content-Type: application/json" \
  "${CURL_AUTH[@]}" \
  "${BACKEND}/centinela/alerts?company_id=${COMPANY_ID}" 2>/dev/null || echo "")

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  RESULTADO=$(curl -s --max-time "$TIMEOUT" \
    "${CURL_AUTH[@]}" \
    "${BACKEND}/agents/centinela-fiscal/alerts" 2>/dev/null || echo "")
fi

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  exit 0
fi

if command -v jq &>/dev/null; then
  COUNT=$(echo "$RESULTADO" | jq '
    if type == "array" then length
    elif .alerts then (.alerts | length)
    elif .alertas then (.alertas | length)
    else 0 end' 2>/dev/null || echo "0")

  if [ "$COUNT" = "0" ] || [ "$COUNT" = "null" ]; then
    exit 0
  fi

  echo "CENTINELA FISCAL — $(date +"%Y-%m-%d %H:%M") (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "${COUNT} alerta(s) fiscal(es) detectada(s):"
  echo ""
  echo "$RESULTADO" | jq -r '
    if type == "array" then .[]
    elif .alerts then .alerts[]
    elif .alertas then .alertas[]
    else empty end |
    "• \(.tipo // .type // .descripcion // "Alerta") — Vence: \(.fecha_vencimiento // .due_date // "N/D")"
  ' 2>/dev/null || echo "$RESULTADO"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Requiere revision HITL antes del cierre de jornada"
else
  echo "$RESULTADO"
fi
