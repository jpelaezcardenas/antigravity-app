# PHASE 2 E2E Testing — Quick Checklist

**Credentials**: contexia.marketing@gmail.com / Lindafea0712  
**Staging URL**: https://antigravity-app-production-175a.up.railway.app  
**Telegram Bot**: @taty_contexia_bot  

---

## T1: Authentication (30 min) — Target: TODAY

- [ ] Desktop browser login → dashboard loads
- [ ] iOS PWA install & login → fullscreen app works
- [ ] Android PWA install & login → fullscreen app works
- [ ] Session persists (close/reopen browser → logged in)

**Status**: ___________  **Issues**: None / [List]

---

## T2: Taty Avatar Chat (30 min) — Target: TODAY

- [ ] Page loads: `/app/taty` visible, input ready
- [ ] In-scope Q: "¿Cuál es el límite de ingresos para Régimen Simple 2026?" → Answer mentions 160 UVT
- [ ] Out-of-scope Q: "¿Debo demandar a mi socio?" → Escalation badge "Requiere revisión de CFO"
- [ ] Citations: At least 1 source + fragment visible
- [ ] Latency: All responses < 4 seconds
- [ ] Multiple questions: "Nueva pregunta" button resets UI cleanly

**Status**: ___________  **Issues**: None / [List]

---

## T3: Taty Internal Chat (20 min) — Target: DAY 2

- [ ] Chat interface loads (or skip if not separate from T2)
- [ ] Same fiscal question answered
- [ ] Chat history scrollable
- [ ] Answers consistent with T2

**Status**: ___________  **Issues**: None / [List]

---

## T4: Telegram Bot (30 min) — Target: DAY 2

- [ ] Open @taty_contexia_bot in Telegram
- [ ] Send: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
- [ ] Response arrives within 6 seconds
- [ ] Answer matches web chat (T2)
- [ ] Send out-of-scope Q → escalation context preserved
- [ ] Multiple rapid messages → all respond (no loss, no duplicates)

**Status**: ___________  **Issues**: None / [List]

---

## T5: Centinela Rules (30 min) — Target: TODAY

- [ ] Trigger R001 UVT: POST `/api/v1/centinela/evaluate` with annual_revenue=10M → Alert
- [ ] Trigger R002 Retención: retention_paid < 3% of service_revenue → Alert (Critical)
- [ ] Trigger R004 Cambio Régimen: last_regime_change_date + dian_notified=false → Alert (Critical)
- [ ] No alerts when data within ranges
- [ ] Risk level calculated: critical if ≥2 critical rules, high if ≥1 critical OR ≥3 warnings
- [ ] Alerts saved to Supabase: `SELECT * FROM centinela_alerts WHERE company_id='ctx-001'`

**Status**: ___________  **Issues**: None / [List]

---

## T6: Centinela Pulso Dashboard (20 min) — Target: DAY 2

- [ ] Pulso tab → alert section visible
- [ ] Trigger alert via API, refresh → alert appears within 5s
- [ ] Severity color-coded (red=critical, orange=high, yellow=medium)
- [ ] Alert title, description, recommendation visible
- [ ] Click alert → expands or shows detail
- [ ] "Marcar como resuelto" → alert removed or marked resolved

**Status**: ___________  **Issues**: None / [List]

---

## T7: Mobile PWA (45 min) — Target: DAY 3

- [ ] iOS: Safari → Add to Home Screen → Opens fullscreen
- [ ] Android: Chrome → Install app → Opens fullscreen
- [ ] All tabs accessible (Pulso, Fiscal, Radar, Config)
- [ ] Taty chat works on mobile (latency acceptable, layout responsive)
- [ ] Text readable (no tiny fonts)
- [ ] Touch buttons responsive (no misclicks)
- [ ] No console errors

**Status**: ___________  **Issues**: None / [List]

---

## T8: Desktop PWA (30 min) — Target: DAY 3

- [ ] Chrome → Install app → Opens standalone window
- [ ] All tabs accessible and functional
- [ ] Responsive to window resize (375px → 1920px)
- [ ] Keyboard navigation: Tab through all elements
- [ ] DevTools → No console errors
- [ ] Performance: FCP < 1.5s, LCP < 3s

**Status**: ___________  **Issues**: None / [List]

---

## T9: Cross-Device Sync (20 min) — Target: DAY 4

- [ ] Desktop Taty chat → iOS PWA → Same history visible
- [ ] Android PWA → Same history
- [ ] Trigger alert on Desktop → iOS/Android Pulso refresh → Alert appears
- [ ] Mark alert resolved on Desktop → iOS/Android reflect change immediately

**Status**: ___________  **Issues**: None / [List]

---

## T10: Performance & Latency (30 min) — Target: DAY 4

- [ ] Taty latency: Ask 5 questions, average < 3s, P95 < 4s
- [ ] Centinela: POST to `/api/v1/centinela/evaluate` → < 1s response
- [ ] Page load: Desktop FCP < 1.5s, LCP < 3s
- [ ] Telegram webhook: < 2s round-trip
- [ ] Memory stable: No growth after 10 min of use

**Status**: ___________  **Issues**: None / [List]

---

## SUMMARY

| Test | Pass | Fail | Issues |
|------|------|------|--------|
| T1: Auth | [ ] | [ ] | |
| T2: Taty Avatar | [ ] | [ ] | |
| T3: Taty Chat | [ ] | [ ] | |
| T4: Telegram | [ ] | [ ] | |
| T5: Centinela | [ ] | [ ] | |
| T6: Pulso | [ ] | [ ] | |
| T7: Mobile PWA | [ ] | [ ] | |
| T8: Desktop PWA | [ ] | [ ] | |
| T9: Sync | [ ] | [ ] | |
| T10: Performance | [ ] | [ ] | |

**Overall**: ✓ PASS / ⚠ PARTIAL / ✗ FAIL

**Sign-off**: _____________________ (Tester) | Date: _________

---

## Next Phase (After All Tests Pass)

1. Regenerate TELEGRAM_BOT_TOKEN via Bot Father
2. Setup vault for secrets (1Password/AWS Secrets Manager)
3. Merge to staging branch
4. Schedule production deployment
5. DAY 2 (2026-05-27): Port llm_analyzer.py, dual A/B orchestration
