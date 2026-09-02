#!/usr/bin/env bash
# Contexia — Pulso Diario (8:00 AM COT / 13:00 UTC)
# Fetches real-time financial pulse from the FastAPI backend (Railway)
# Output: formatted daily financial briefing (stdout) or empty on failure
set -euo pipefail

BACKEND="https://antigravity-app-production-175a.up.railway.app/api/v1"
TIMEOUT=15

# Build auth header if HERMES_BRIDGE_TOKEN is set
CURL_AUTH=()
if [ -n "${HERMES_BRIDGE_TOKEN:-}" ]; then
  CURL_AUTH=(-H "Authorization: Bearer ${HERMES_BRIDGE_TOKEN}")
fi

# Try the primary Pulso endpoint first (POST since Aug 2026 backend change)
PULSO=$(curl -s --max-time "$TIMEOUT" -X POST \
  -H "Content-Type: application/json" \
  "${CURL_AUTH[@]}" \
  "${BACKEND}/agents/pulso-diario/summary" 2>/dev/null || echo "")

# Fallback to /financials (GET) if pulso-diario/summary fails
if [ -z "$PULSO" ] || echo "$PULSO" | grep -q '"detail"'; then
  PULSO=$(curl -s --max-time "$TIMEOUT" \
    "${CURL_AUTH[@]}" \
    "${BACKEND}/financials" 2>/dev/null || echo "")
fi

# If both failed, stay silent (watchdog pattern)
if [ -z "$PULSO" ] || echo "$PULSO" | grep -q '"detail"'; then
  exit 0
fi

# Extract key fields with jq, fallback to raw JSON
if command -v jq &>/dev/null; then
  FECHA=$(date +"%Y-%m-%d %H:%M" -u -5h 2>/dev/null || date +"%Y-%m-%d %H:%M")
  CAJA=$(echo "$PULSO" | jq -r '.caja_real // .caja_real_hoy // .cash // empty' 2>/dev/null || echo "N/D")
  INGRESOS=$(echo "$PULSO" | jq -r '.ingresos_hoy // .ventas // .revenue // empty' 2>/dev/null || echo "N/D")
  GASTOS=$(echo "$PULSO" | jq -r '.gastos_hoy // .expenses // empty' 2>/dev/null || echo "N/D")
  RESERVA=$(echo "$PULSO" | jq -r '.reserva_tax // .tax_reserve // empty' 2>/dev/null || echo "N/D")

  echo "PULSO DIARIO — ${FECHA} (COT)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Caja Real:        $${CAJA} COP"
  echo "Ingresos (ayer):  $${INGRESOS} COP"
  echo "Gastos (ayer):    $${GASTOS} COP"
  [ "$RESERVA" != "" ] && echo "Reserva Tax:      $${RESERVA} COP"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Fuente: Shadow GL (cuenta 1110 Bancos) — Cliente Cero"
else
  echo "PULSO DIARIO — $(date +"%Y-%m-%d %H:%M")"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$PULSO"
fi
