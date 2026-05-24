# E2E Testing — Fast Track (Cliente + Admin)
**Objetivo**: Validar TODO el sistema como cliente + verificar acceso admin  
**Duración**: 2-3 horas  
**Ambiente**: Staging (Production-175a)  
**Credenciales Cliente**: contexia.marketing@gmail.com / Lindafea0712  

---

## Recomendación: Testing Por Rol

### ROL 1: Cliente (Contexia SAS)
**Cuenta**: contexia.marketing@gmail.com / Lindafea0712  
**Permisos**: Acceso a dashboard, Taty, Centinela, Telegram  
**Objetivo**: Verificar que cliente puede usar TODO

### ROL 2: Admin (TBD)
**Cuenta**: ¿Necesitas crear una o ya existe?  
**Permisos**: (a definir) - ¿config global? ¿multi-cliente? ¿audit logs?  
**Objetivo**: Verificar que admin puede supervisar clientes

---

## FAST-TRACK TESTING PLAN

### **BLOQUE 1: Autenticación & Acceso (15 min)**

#### Test 1.1: Login como Cliente
```
1. Abre: https://antigravity-app-production-175a.up.railway.app
2. Email: contexia.marketing@gmail.com
3. Password: Lindafea0712
4. ✓ Dashboard carga
5. ✓ Ver 4 tabs: Pulso, Fiscal, Radar, Config
6. ✓ Usuario visible en top bar
```

**Expected**: Login successful, dashboard visible, no 401/403 errors

#### Test 1.2: Session Persistence
```
1. Cierra navegador completamente
2. Reabre URL
3. ✓ Dashboard carga sin pedir login nuevamente
```

**Expected**: Session automática (JWT en localStorage/cookie)

---

### **BLOQUE 2: Taty Contadora — CORE FEATURE (30 min)**

#### Test 2.1: Avatar Chat (Dashboard)
```
Pregunta In-Scope (Fiscal/DIAN):
  Q: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
  ✓ Response en < 4 segundos
  ✓ Menciona "160 UVT" y "$8.38M COP"
  ✓ Muestra citations (source + fragment)
  ✓ Latency badge visible
```

#### Test 2.2: Pregunta Out-of-Scope (Escalación)
```
  Q: "¿Debo demandar a mi socio?"
  ✓ Response incluye badge "⚠️ Requiere revisión de CFO"
  ✓ Botón "Contactar CFO" visible
```

#### Test 2.3: Multiple Questions
```
  Q: "¿Qué es la retención en la fuente?"
  Q: "¿Cómo funciona la factura electrónica?"
  ✓ Ambas responden correctamente
  ✓ Botón "Nueva pregunta" limpia input
```

#### Test 2.4: Error Handling
```
  Envía pregunta vacía → Send button deshabilitado
  Envía 500+ caracteres → Response normal
  Caracteres especiales (ñ, á, €) → UTF-8 correcto
```

**Success Criteria**: Taty responde a todas las preguntas in-scope, marca escalaciones, latencia < 4s promedio

---

### **BLOQUE 3: Centinela Rules Engine (20 min)**

#### Test 3.1: Evaluación Automática (via API)
```
curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/centinela/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "ctx-001",
    "data": {
      "regimen": "Régimen Simple",
      "annual_revenue": 10000000
    }
  }'

✓ Response: Alert R001 (UVT Excedido)
✓ Severity: "warning"
✓ Description menciona el exceso
```

#### Test 3.2: Otra Regla (Retención)
```
  "regime": "Régimen Común",
  "service_revenue": 1000000,
  "retention_paid": 5000  (< 3%)

✓ Response: Alert R002 (Retención No Pagada)
✓ Severity: "critical"
```

#### Test 3.3: Sin Alertas (Datos Sanos)
```
  "annual_revenue": 5000000 (< 8.38M)

✓ Response: empty alerts list (no alert triggered)
```

**Success Criteria**: 10 reglas evaluadas correctamente, severidades correctas

---

### **BLOQUE 4: Centinela Pulso Dashboard (15 min)**

#### Test 4.1: Alertas en Dashboard
```
1. Click "Pulso" tab
2. Busca sección "Centinela" o "Alertas"
3. Verifica que alert R001 aparece
4. ✓ Color: rojo (critical) o amarillo (warning) según severity
```

#### Test 4.2: Semáforo Status
```
Esperado después de trigger R001 + R002 (2 critical):
  Semáforo: 🔴 ROJO (risk_level = "critical")
```

#### Test 4.3: Interacción con Alertas
```
Click en alert → Expande detalles
"Marcar como resuelto" → Alert desaparece
Refresh → Alert removido o en "Histórico"
```

**Success Criteria**: Alerts visibles, color-coded, interactivos

---

### **BLOQUE 5: Telegram Bot (10 min)**

#### Test 5.1: Enviar Mensaje
```
1. Abre Telegram → @taty_contexia_bot
2. Envía: "¿Cuál es el límite de ingresos para Régimen Simple 2026?"
3. ✓ Response en 4-6 segundos
4. ✓ Respuesta IGUAL a la del web chat (T2.1)
```

#### Test 5.2: Escalación en Telegram
```
Envía: "¿Debo demandar a mi socio?"
✓ Response menciona que requiere revisión humana
```

**Success Criteria**: Bot responde, respuestas consistentes con web

---

### **BLOQUE 6: Fiscal Tab (10 min)**

#### Test 6.1: Explorar Datos
```
1. Click "Fiscal" tab
2. ✓ Ver tablas de impuestos, retenciones, facturación
3. ✓ Si hay drill-down: click en row → detalles cargan
```

#### Test 6.2: Responsive Design
```
1. Resize navegador a mobile (375px)
2. ✓ Tablas scrolleables horizontalmente (no overflow)
3. ✓ Texto legible (no fonts tiny)
```

**Success Criteria**: Datos visibles, responsive

---

### **BLOQUE 7: Mobile PWA (15 min) — OPCIONAL pero RECOMENDADO**

#### Test 7.1: iOS o Android
```
1. Abre en teléfono: https://antigravity-app-production-175a.up.railway.app
2. Add to Home Screen
3. Launch from home screen
4. ✓ Fullscreen app (no browser chrome)
5. Login → Dashboard visible
```

#### Test 7.2: Taty en Mobile
```
Haz misma pregunta fiscal que en T2.1
✓ Response < 5 segundos (un poco más lento que desktop ok)
✓ Layout responsive
✓ Botón send tappable (sin misclicks)
```

**Success Criteria**: App instala, Taty funciona, responsive

---

## TESTING CHECKLIST — FAST TRACK

```
BLOQUE 1: Autenticación (15 min)
  [ ] 1.1 Login como cliente → dashboard
  [ ] 1.2 Session persiste

BLOQUE 2: Taty (30 min)
  [ ] 2.1 Pregunta fiscal → responde correctamente
  [ ] 2.2 Pregunta out-of-scope → escalación badge
  [ ] 2.3 Múltiples preguntas → todas responden
  [ ] 2.4 Error handling (empty, long, special chars)

BLOQUE 3: Centinela (20 min)
  [ ] 3.1 Evalúa R001 (UVT) correctamente
  [ ] 3.2 Evalúa R002 (Retención) correctamente
  [ ] 3.3 Sin alertas cuando datos sanos

BLOQUE 4: Pulso Dashboard (15 min)
  [ ] 4.1 Alertas visibles en dashboard
  [ ] 4.2 Semáforo status correcto
  [ ] 4.3 Alertas interactivas (expandir, resolver)

BLOQUE 5: Telegram (10 min)
  [ ] 5.1 Bot responde correctamente
  [ ] 5.2 Escalaciones funcionan en Telegram

BLOQUE 6: Fiscal Tab (10 min)
  [ ] 6.1 Datos visibles
  [ ] 6.2 Responsive design

BLOQUE 7: Mobile PWA (15 min) OPCIONAL
  [ ] 7.1 PWA instala y corre fullscreen
  [ ] 7.2 Taty funciona en mobile

═══════════════════════════════
TOTAL TIME: 2-3 horas
STATUS: [ ] PASS / [ ] FAIL
═══════════════════════════════
```

---

## CREDENCIALES & ACCESO

| Item | Valor |
|------|-------|
| **Cliente Email** | contexia.marketing@gmail.com |
| **Client Password** | Lindafea0712 |
| **Company ID** | ctx-001 (Contexia SAS) |
| **Staging URL** | https://antigravity-app-production-175a.up.railway.app |
| **Telegram Bot** | @taty_contexia_bot |
| **Supabase Project** | kpynymwghfwshvcvevxq |

---

## ACCESO ADMIN (TBD)

**Preguntas**:
1. ¿Existe ya una cuenta de admin?
2. ¿Qué permisos tiene? (config global, ver todos los clientes, audit logs, etc.)
3. ¿Debería crear un usuario "admin" o probamos con cliente primero?

**Recomendación**: Primero prueba TODO como **cliente** (contexia.marketing@gmail.com). Si todo funciona como cliente, luego podemos:
- Crear usuario admin (si no existe)
- Probar funcionalidades admin
- Verificar separación de permisos

---

## FLUJO RECOMENDADO

### **DÍA DE HOY (2-3 horas)**

1. **BLOQUE 1** (15 min): Auth ✓
2. **BLOQUE 2** (30 min): Taty — core feature ✓
3. **BLOQUE 3** (20 min): Centinela rules ✓
4. **BLOQUE 4** (15 min): Pulso dashboard ✓
5. **BLOQUE 5** (10 min): Telegram ✓
6. **BLOQUE 6** (10 min): Fiscal tab ✓
7. **BLOQUE 7** (15 min): Mobile (si tiempo disponible)

### **DESPUÉS (DAY 2 — Lunes 2026-05-27)**

Si TODO pasa:
- Merge PR to develop
- Port llm_analyzer.py from EAFIT
- Implement dual A/B orchestration
- Neurocontabilidad real-time indexing
- Centinela cron (nightly evaluation)

Si algo falla:
- Fix bug
- Re-test
- Document in issue
- Merge cuando todo verde

---

## TROUBLESHOOTING RÁPIDO

| Problema | Solución |
|----------|----------|
| Login falla 401 | Verifica credenciales, check Supabase auth.users |
| Taty error "desconocido" | Check backend logs, verify LLM provider (Groq) up |
| Centinela no retorna alertas | Check Supabase connection, verify company_id |
| Telegram no responde | Check webhook logs, verify HMAC signature |
| PWA no instala | Clear cache, try incognito, check PWA manifest |

---

## SIGN-OFF

Una vez completes los 6 bloques principales:

**✓ READY FOR**:
- [ ] Merge to develop
- [ ] DAY 2 implementation (lunes)
- [ ] Production deployment (después de hardening)

**✗ ISSUES FOUND**:
- [ ] Create GitHub issue per bug
- [ ] Fix + re-test
- [ ] Document in CLAUDE.md

---

**Status**: Ready to execute  
**Last Updated**: 2026-05-24  
**Estimated Time**: 2-3 hours (6 bloques principales)  
**Optional Time**: +15 min (mobile PWA)
