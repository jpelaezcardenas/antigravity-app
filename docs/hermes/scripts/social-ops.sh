#!/usr/bin/env bash
# Contexia — Social Ops Briefing (8:00 AM COT / 13:00 UTC, lunes-viernes)
# Pipeline de contenido: ideas pendientes, metricas, inbox, aprobaciones
# Watchdog pattern: silencio si pipeline limpio, reporte si hay items pendientes
set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app/api/v1"
COMPANY_ID="ff1a8b7c-b0a1-422e-bc48-fac6242be027"
TIMEOUT=20

CURL_AUTH=()
if [ -n "${HERMES_BRIDGE_TOKEN:-}" ]; then
  CURL_AUTH=(-H "Authorization: Bearer ${HERMES_BRIDGE_TOKEN}")
fi

RESULTADO=$(curl -s --max-time "$TIMEOUT" \
  "${CURL_AUTH[@]}" \
  "${BACKEND}/social-ops/briefing?company_id=${COMPANY_ID}" 2>/dev/null || echo "")

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  RESULTADO=$(curl -s --max-time "$TIMEOUT" \
    "${CURL_AUTH[@]}" \
    "${BACKEND}/channels/social-ops/pipeline" 2>/dev/null || echo "")
fi

if [ -z "$RESULTADO" ] || echo "$RESULTADO" | grep -q '"detail"'; then
  exit 0
fi

if command -v jq &>/dev/null; then
  PENDIENTES=$(echo "$RESULTADO" | jq '
    (.pendientes // .pending // .ideas_pendientes // []) | length
  ' 2>/dev/null || echo "0")

  APROBACIONES=$(echo "$RESULTADO" | jq '
    (.aprobaciones_pendientes // .pending_approvals // []) | length
  ' 2>/dev/null || echo "0")

  if [ "$PENDIENTES" = "0" ] && [ "$APROBACIONES" = "0" ]; then
    exit 0
  fi

  echo "SOCIAL OPS — $(date +"%Y-%m-%d %H:%M") (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  [ "$PENDIENTES" != "0" ] && echo "Ideas pendientes: ${PENDIENTES}"
  [ "$APROBACIONES" != "0" ] && echo "Aprobaciones requeridas: ${APROBACIONES}"
  echo ""
  echo "$RESULTADO" | jq -r '
    (.aprobaciones_pendientes // .pending_approvals // []) | .[] |
    "• [APROBAR] \(.titulo // .title // .content // "Contenido pendiente")"
  ' 2>/dev/null
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Social Ops — HITL requerido para publicar"
else
  echo "$RESULTADO"
fi
