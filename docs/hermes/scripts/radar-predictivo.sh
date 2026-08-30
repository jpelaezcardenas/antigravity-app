#!/usr/bin/env bash
# Contexia — Radar Predictivo (6:00 AM COT / 11:00 UTC, lunes-viernes)
# Prediccion de riesgos tributarios y flujo de caja 30-90 dias
# Watchdog pattern: silencio si sin riesgos, alerta si hay predicciones criticas
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
  "${BACKEND}/radar?company_id=${COMPANY_ID}" 2>/dev/null || echo "")

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  RESULTADO=$(curl -s --max-time "$TIMEOUT" \
    "${CURL_AUTH[@]}" \
    "${BACKEND}/agents/radar/predictions" 2>/dev/null || echo "")
fi

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  exit 0
fi

if command -v jq &>/dev/null; then
  RIESGO=$(echo "$RESULTADO" | jq -r '.riesgo_nivel // .risk_level // "desconocido"' 2>/dev/null || echo "desconocido")

  if [ "$RIESGO" = "bajo" ] || [ "$RIESGO" = "low" ] || [ "$RIESGO" = "none" ]; then
    exit 0
  fi

  FECHA=$(date +"%Y-%m-%d")
  echo "RADAR PREDICTIVO — ${FECHA} (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Nivel de riesgo: ${RIESGO}"
  echo ""
  echo "$RESULTADO" | jq -r '
    (.predicciones // .predictions // []) |
    .[] |
    "• \(.descripcion // .description // "Riesgo") — Horizonte: \(.horizonte_dias // .days // "N/D") dias — Impacto: \(.monto_estimado // .estimated_amount // "N/D") COP"
  ' 2>/dev/null || echo "$RESULTADO"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Radar Predictivo — 30-90 dias ahead"
else
  echo "$RESULTADO"
fi
