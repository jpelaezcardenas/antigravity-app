# Pulso Dashboard & Mobile PWA — Mock Data Strategy + Real Data Activation
**Contexto**: Testing sin DIAN/SIIGO/Sync Manager, pero listo para ferias de emprendimiento  
**Objetivo**: Validar UX/UI y lógica con datos mock, transicionar a datos reales cuando integraciones listas  
**Crítico para**: Ferias, investor pitch, mobile experience

---

## PARTE 1: TESTING ACTUAL (HOY) — DATOS MOCK

### Estado Actual (2026-05-24)

| Integración | Status | Data Source |
|-------------|--------|-------------|
| **DIAN** | ❌ No conectado | Datos mock en Supabase |
| **SIIGO** | ❌ No conectado | Datos mock en Supabase |
| **Sync Manager** | ❌ No conectado | Datos mock en Supabase |
| **Data Lake** | ❌ No poblado | Seed data + mock |
| **Centinela Rules** | ✅ Funciona | Evalúa mock financial data |
| **Pulso Dashboard** | ✅ Funciona | Lee mock data de agent_profiles |

---

## BLOQUE 4 EXTENDIDO: PULSO DASHBOARD TESTING CON MOCK DATA

### Arquitectura Mock

```
┌─────────────────────────────────────┐
│  Pulso Dashboard (React)            │
│  ├─ Metrics (KPIs, semáforo)       │
│  ├─ Centinela Alerts               │
│  └─ Financial Summary              │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Supabase (Mock Data)               │
│  ├─ agent_profiles (empresa)        │
│  ├─ centinela_alerts (rules)        │
│  ├─ financial_snapshot (mock)       │ ← NEW TABLE
│  └─ conversation_messages (Taty)    │
└─────────────────────────────────────┘
```

### Paso 1: Crear Tabla Mock `financial_snapshot`

```sql
CREATE TABLE financial_snapshot (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES agent_profiles(company_id),
  period_date DATE,
  
  -- KPIs Pulso
  ingreso_anual NUMERIC,
  utilidad_neta NUMERIC,
  tasa_impuesto NUMERIC,
  efectivo_disponible NUMERIC,
  deuda_total NUMERIC,
  
  -- Indicators
  cash_health TEXT, -- 'sano', 'alerta', 'crítico'
  tax_compliance TEXT, -- 'compliant', 'pendiente', 'riesgo'
  
  -- Metadata
  data_source TEXT, -- 'mock', 'siigo', 'dian'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_financial_snapshot_company ON financial_snapshot(company_id);
CREATE INDEX idx_financial_snapshot_date ON financial_snapshot(period_date DESC);
```

### Paso 2: Seed Mock Data para Contexia

```sql
INSERT INTO financial_snapshot (company_id, period_date, ingreso_anual, utilidad_neta, tasa_impuesto, efectivo_disponible, deuda_total, cash_health, tax_compliance, data_source)
VALUES (
  (SELECT company_id FROM agent_profiles WHERE nombre_empresa = 'Contexia SAS'),
  '2026-05-24',
  85000000,  -- $85M ingresos anuales
  12750000,  -- $12.75M utilidad neta
  0.28,      -- 28% tasa impuesto
  4200000,   -- $4.2M efectivo disponible
  15000000,  -- $15M deuda total
  'sano',    -- Cash health indicator
  'compliant', -- Tax compliance
  'mock'     -- Data source: mock (not SIIGO)
);

-- Seed data para FEREZ SAS y Importaciones Martinez
INSERT INTO financial_snapshot (company_id, period_date, ingreso_anual, utilidad_neta, tasa_impuesto, efectivo_disponible, deuda_total, cash_health, tax_compliance, data_source)
VALUES (
  (SELECT company_id FROM agent_profiles WHERE nombre_empresa = 'FEREZ SAS'),
  '2026-05-24',
  42500000,
  4250000,
  0.25,
  1700000,
  8000000,
  'alerta',  -- ⚠️ Efectivo bajo
  'pendiente',
  'mock'
);

INSERT INTO financial_snapshot (company_id, period_date, ingreso_anual, utilidad_neta, tasa_impuesto, efectivo_disponible, deuda_total, cash_health, tax_compliance, data_source)
VALUES (
  (SELECT company_id FROM agent_profiles WHERE nombre_empresa = 'Importaciones Martinez'),
  '2026-05-24',
  125000000,
  18750000,
  0.30,
  6200000,
  22000000,
  'sano',
  'riesgo',  -- ⚠️ Deuda alto vs utilidad
  'mock'
);
```

### Paso 3: API Endpoint para Pulso (Backend)

**Archivo**: `apps/backend/presentation/pulso_endpoints.py`

```python
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime, timedelta

pulso_router = APIRouter()

@pulso_router.get("/api/v1/pulso/dashboard/{company_id}")
async def get_pulso_dashboard(company_id: str):
    """
    Retorna datos para Pulso dashboard:
    - Financial KPIs
    - Centinela risk level
    - Semáforo status
    - Cash health indicator
    """
    try:
        supabase = get_supabase()
        
        # 1. Fetch financial snapshot (mock or real)
        financial = supabase.table("financial_snapshot") \
            .select("*") \
            .eq("company_id", company_id) \
            .order("period_date", desc=True) \
            .limit(1) \
            .execute()
        
        if not financial.data:
            raise ValueError(f"No financial data for {company_id}")
        
        fin_data = financial.data[0]
        
        # 2. Fetch Centinela alerts (las últimas)
        alerts = supabase.table("centinela_alerts") \
            .select("rule_id, severity, title, created_at") \
            .eq("company_id", company_id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .execute()
        
        # 3. Calculate risk level
        critical_count = sum(1 for a in alerts.data if a["severity"] == "critical")
        warning_count = sum(1 for a in alerts.data if a["severity"] == "warning")
        
        if critical_count >= 2:
            risk_level = "critical"
            semaforo = "🔴"
        elif critical_count >= 1 or warning_count >= 3:
            risk_level = "high"
            semaforo = "🟡"
        elif warning_count >= 1:
            risk_level = "medium"
            semaforo = "🟡"
        else:
            risk_level = "low"
            semaforo = "🟢"
        
        # 4. Calculate KPIs
        ingreso = fin_data["ingreso_anual"]
        utilidad = fin_data["utilidad_neta"]
        margen = (utilidad / ingreso * 100) if ingreso > 0 else 0
        
        # 5. Compose response
        return {
            "company_id": company_id,
            "period": fin_data["period_date"],
            
            # KPIs
            "kpis": {
                "ingreso_anual": ingreso,
                "utilidad_neta": utilidad,
                "margen_neto_pct": round(margen, 2),
                "efectivo_disponible": fin_data["efectivo_disponible"],
                "deuda_total": fin_data["deuda_total"],
                "data_source": fin_data["data_source"],  # "mock" or "siigo"
            },
            
            # Health Indicators
            "indicators": {
                "cash_health": fin_data["cash_health"],  # sano, alerta, crítico
                "tax_compliance": fin_data["tax_compliance"],  # compliant, pendiente, riesgo
            },
            
            # Centinela
            "centinela": {
                "active_alerts": len(alerts.data),
                "critical_alerts": critical_count,
                "warning_alerts": warning_count,
                "risk_level": risk_level,
                "semaforo": semaforo,
                "recent_alerts": alerts.data[:5],  # Top 5
            },
            
            # Metadata
            "timestamp": datetime.now().isoformat(),
            "mode": "mock" if fin_data["data_source"] == "mock" else "production",
        }
        
    except Exception as e:
        logger.error(f"Error fetching Pulso data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Paso 4: Frontend Component (React)

**Archivo**: `contexia-app/components/pulso/PulsoView.tsx`

```typescript
"use client";

import { useState, useEffect } from "react";
import type { PulsoDashboardData } from "@/lib/types/pulso";

export function PulsoView({ company_id = "ctx-001" }) {
  const [data, setData] = useState<PulsoDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `/api/v1/pulso/dashboard/${company_id}`
        );
        if (!response.ok) throw new Error("Failed to load Pulso data");
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [company_id]);

  if (loading) {
    return <div className="p-6 text-center">Cargando Pulso...</div>;
  }

  if (error || !data) {
    return <div className="p-6 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* HEADER: Semáforo Status */}
      <div className="flex items-center gap-4 p-4 rounded-lg bg-surface-elevated border border-outline">
        <div className="text-6xl">{data.centinela.semaforo}</div>
        <div className="flex-1">
          <h2 className="text-headline-lg font-semibold text-on-surface">
            Estado Fiscal Actual
          </h2>
          <p className="text-body-md text-on-surface-variant">
            Risk Level:{" "}
            <span
              className={`font-bold ${
                data.centinela.risk_level === "critical"
                  ? "text-error"
                  : "text-warning"
              }`}
            >
              {data.centinela.risk_level.toUpperCase()}
            </span>
          </p>
          <p className="text-label-sm text-on-surface-variant">
            Data Source:{" "}
            <span className="bg-surface-variant px-2 py-1 rounded">
              {data.mode === "mock" ? "🔄 Mock (Testing)" : "✓ Real (SIIGO)"}
            </span>
          </p>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Ingresos */}
        <div className="p-4 rounded-lg bg-surface-elevated border border-outline">
          <p className="text-label-sm text-on-surface-variant mb-1">
            Ingresos Anuales
          </p>
          <p className="text-headline-md font-bold text-on-surface">
            ${(data.kpis.ingreso_anual / 1000000).toFixed(1)}M
          </p>
          <p className="text-caption text-on-surface-variant">
            COP 2026
          </p>
        </div>

        {/* Utilidad */}
        <div className="p-4 rounded-lg bg-surface-elevated border border-outline">
          <p className="text-label-sm text-on-surface-variant mb-1">
            Utilidad Neta
          </p>
          <p className="text-headline-md font-bold text-on-surface">
            ${(data.kpis.utilidad_neta / 1000000).toFixed(2)}M
          </p>
          <p className="text-caption text-on-surface-variant">
            Margen: {data.kpis.margen_neto_pct}%
          </p>
        </div>

        {/* Efectivo */}
        <div className="p-4 rounded-lg bg-surface-elevated border border-outline">
          <p className="text-label-sm text-on-surface-variant mb-1">
            Efectivo Disponible
          </p>
          <p className="text-headline-md font-bold text-on-surface">
            ${(data.kpis.efectivo_disponible / 1000000).toFixed(2)}M
          </p>
          <p
            className={`text-caption ${
              data.indicators.cash_health === "sano"
                ? "text-success"
                : data.indicators.cash_health === "alerta"
                  ? "text-warning"
                  : "text-error"
            }`}
          >
            {data.indicators.cash_health.toUpperCase()}
          </p>
        </div>
      </div>

      {/* CENTINELA ALERTS */}
      <div className="p-4 rounded-lg bg-surface-elevated border border-outline">
        <h3 className="text-headline-sm font-semibold text-on-surface mb-4">
          ⚠️ Alertas Fiscales (Centinela)
        </h3>

        {data.centinela.active_alerts === 0 ? (
          <p className="text-body-sm text-success">
            ✓ No hay alertas fiscales activas
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {data.centinela.recent_alerts.map((alert) => (
              <div
                key={alert.rule_id}
                className={`p-3 rounded border ${
                  alert.severity === "critical"
                    ? "bg-error/10 border-error/30"
                    : "bg-warning/10 border-warning/30"
                }`}
              >
                <p className="font-semibold text-sm text-on-surface">
                  {alert.title}
                </p>
                <p className="text-xs text-on-surface-variant mt-1">
                  {alert.rule_id} • {alert.severity}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* DATA SOURCE BADGE */}
      {data.mode === "mock" && (
        <div className="p-3 rounded-lg bg-info/10 border border-info/30">
          <p className="text-label-sm font-semibold text-info">
            🔄 Modo Testing — Datos Mock
          </p>
          <p className="text-caption text-info/80 mt-1">
            Cuando SIIGO, DIAN y Sync Manager se conecten, estos datos se
            actualizarán automáticamente.
          </p>
        </div>
      )}
    </div>
  );
}
```

### Paso 5: Test Checklist — Pulso con Mock Data

```
✓ SETUP
  [ ] Crear tabla financial_snapshot en Supabase
  [ ] Seed mock data para Contexia, FEREZ, Importaciones
  [ ] Implementar GET /api/v1/pulso/dashboard/{company_id}
  [ ] Crear PulsoView.tsx component

✓ TESTING DASHBOARD
  [ ] Login como contexia.marketing@gmail.com
  [ ] Click Pulso tab
  [ ] Verificar:
    [ ] KPI cards (Ingresos $85M, Utilidad $12.75M, Efectivo $4.2M)
    [ ] Cash health: "sano" (green)
    [ ] Tax compliance: "compliant"
    [ ] Semáforo: 🟢 (green) porque no hay alertas críticas
  [ ] Data Source badge: "🔄 Mock (Testing)"
  
✓ TESTING WITH ALERTS
  [ ] Manualmente trigger R001 (UVT) via Centinela API
  [ ] Refresh Pulso
  [ ] Verificar:
    [ ] Semáforo cambia a 🟡 (yellow)
    [ ] Risk level: "medium" o "high"
    [ ] Alert card visible con descripción

✓ TESTING FEREZ COMPANY
  [ ] Cambiar company_id a FEREZ SAS
  [ ] Verificar:
    [ ] Datos diferentes ($42.5M ingreso)
    [ ] Cash health: "alerta" (yellow)
    [ ] Semáforo: 🟡 (alerta)

✓ RESPONSIVE
  [ ] Desktop: 3-column KPI grid
  [ ] Tablet: 2-column grid
  [ ] Mobile: 1-column stack

✓ MOCK DATA BADGE
  [ ] Badge visible: "🔄 Modo Testing — Datos Mock"
  [ ] Message explains: "Cuando SIIGO... se conecte, se actualizarán"
```

---

## PARTE 2: ACTIVACIÓN CON DATOS REALES (DESPUÉS)

### Cuando SIIGO + DIAN + Sync Manager Estén Listos

**Timeline**: Junio/Julio 2026 (después de MVP)

#### Fase 1: Conectar SIIGO (Accounting Data)

```python
# NEW: apps/backend/integrations/siigo_connector.py

class SiigoConnector:
    """
    Fetch financial data from SIIGO API
    Replace mock data in financial_snapshot
    """
    
    async def fetch_company_financials(company_id: str, month: int, year: int):
        """
        1. Get Contexia auth token (stored in Supabase secrets)
        2. Call SIIGO API: GET /accounting/reports/balance-sheet
        3. Extract: ingresos, utilidad, efectivo, deuda
        4. Update financial_snapshot table
        5. Trigger Centinela evaluation
        """
        # Implementation: OAuth to SIIGO, fetch, parse XML, store
        pass
```

**Changes to financial_snapshot table**:
```sql
ALTER TABLE financial_snapshot ADD COLUMN siigo_sync_date TIMESTAMP;
ALTER TABLE financial_snapshot ADD COLUMN siigo_document_id TEXT;
-- Now queries know: data_source = 'siigo' means real data
```

#### Fase 2: Conectar DIAN (Tax Compliance Data)

```python
# NEW: apps/backend/integrations/dian_connector.py

class DIANConnector:
    """
    Fetch DIAN compliance data:
    - UVT limits (automatically updated 2026-01-01)
    - Retention obligations
    - Related party declarations
    - Tax debt status
    """
    
    async def fetch_company_compliance(nit: str):
        """
        1. Query DIAN Public APIs (requires DIAN credentials)
        2. Check: regime, debt, retention status
        3. Populate centinela_alerts if violations
        4. Update tax_compliance indicator
        """
        pass
```

#### Fase 3: Conectar Sync Manager + Data Lake

```python
# NEW: apps/backend/integrations/syncmanager_connector.py

class SyncManagerConnector:
    """
    Real-time causalización (causation linking):
    - Invoice (factura) → Accounting entry (asiento)
    - Payment → Cash flow
    - Retention → Tax obligation
    """
    
    async def sync_accounting_with_causation(company_id: str):
        """
        1. Fetch from Sync Manager: XL de clientes, causación info
        2. Validate: Every invoice has matching accounting entry
        3. Update data_lake with reconciled data
        4. Centinela evaluates against real causal chain
        """
        pass
```

### Cómo Transicionar (Sin Reescribir Código)

**Strategy: Conditional Data Source**

```python
# apps/backend/services/financial_service.py

class FinancialDataService:
    """
    Abstraction layer: same interface, different sources
    """
    
    async def get_company_financials(company_id: str, source="auto"):
        """
        source = "auto" → Use best available:
          1. If SIIGO connected: fetch from SIIGO
          2. Else if mock exists: use mock
          3. Else: error
        """
        
        # Query agent_profiles to see what integrations are active
        integrations = await get_integrations(company_id)
        
        if integrations["siigo_connected"]:
            # Phase 2+: Real data
            return await SiigoConnector.fetch(company_id)
        else:
            # Phase 1 (now): Mock data
            return await MockDataService.fetch(company_id)
```

**Frontend: Same Component, Different Data**

```typescript
// PulsoView.tsx works EXACTLY THE SAME
// Only difference: data.mode changes from "mock" to "production"

{data.mode === "mock" && (
  <div className="p-3 rounded-lg bg-info/10">
    <p className="text-label-sm">🔄 Modo Testing — Datos Mock</p>
  </div>
)}

{data.mode === "production" && (
  <div className="p-3 rounded-lg bg-success/10">
    <p className="text-label-sm">✓ Datos Reales desde SIIGO</p>
  </div>
)}
```

---

## PARTE 3: BLOQUE 7 — MOBILE PWA (PARA FERIAS)

### Por Qué es Crítico para Ferias

| Aspecto | Importancia |
|---------|------------|
| **Visual** | Investors ven "app real", no prototipo web |
| **Engagement** | Puedes pasar teléfono, ellos interactúan |
| **Credibilidad** | iOS/Android = product-market fit |
| **Memorable** | "Vi el app en vivo en su teléfono" |

### Testing Mobile PWA — Full Checklist

#### Test 7.1: Installation (iOS)
```
1. iPhone: Safari → URL
2. Tap Share → Add to Home Screen
3. ✓ App icon on home screen
4. Tap to launch
5. ✓ Fullscreen (no Safari chrome)
6. ✓ App name "Contexia" visible in status bar
```

#### Test 7.2: Installation (Android)
```
1. Android: Chrome → URL
2. Tap menu → Install app
3. ✓ Icon on home screen
4. Tap to launch
5. ✓ Fullscreen, no Chrome UI
```

#### Test 7.3: Mobile UI — Pulso
```
1. Launch PWA on mobile
2. Login: contexia.marketing@gmail.com / Lindafea0712
3. Bottom nav → Pulso
4. Verify:
   [ ] Semáforo 🟢 visible (large)
   [ ] KPI cards stack vertically (1 column)
   [ ] Text readable (font size ≥ 16px)
   [ ] Buttons tappable (≥ 44x44 pt)
   [ ] Alerts section scrollable
```

#### Test 7.4: Mobile UI — Taty Chat
```
1. Navigate to Taty page
2. Ask: "¿Cuál es el límite de ingresos para Régimen Simple?"
3. Verify:
   [ ] Input field at bottom (sticky)
   [ ] Send button reachable with thumb
   [ ] Response cards full-width
   [ ] Citations expandable without scroll
   [ ] Loading spinner visible
```

#### Test 7.5: Mobile UI — Telegram
```
1. Open Telegram on mobile
2. @taty_contexia_bot
3. Send same question
4. ✓ Response < 6 seconds
5. ✓ Readable message format
```

#### Test 7.6: Performance Mobile
```
1. Chrome DevTools → Network tab (throttle to 4G)
2. Load Pulso page
3. Measure:
   [ ] FCP (First Contentful Paint) < 2s
   [ ] LCP (Largest Contentful Paint) < 4s
   [ ] Memory < 60MB
4. No layout shift when semáforo loads
```

#### Test 7.7: Offline (if service worker implemented)
```
1. Load app on mobile
2. Go offline (Airplane mode)
3. Try to ask Taty → Error or cached response
4. Go online
5. ✓ Works again
```

### Mobile PWA Checklist

```
✓ INSTALLATION
  [ ] iOS PWA installs and launches fullscreen
  [ ] Android PWA installs and launches fullscreen
  [ ] App name "Contexia" shows in title bar

✓ PULSO DASHBOARD (Mobile)
  [ ] Semáforo displays prominently
  [ ] KPI cards stack 1-column
  [ ] No horizontal scroll
  [ ] Alerts scrollable vertically

✓ TATY CHAT (Mobile)
  [ ] Input field sticky at bottom
  [ ] Send button thumb-friendly
  [ ] Response cards readable
  [ ] Citations expandable

✓ TELEGRAM (Mobile)
  [ ] Bot messages display clearly
  [ ] Formatting preserved
  [ ] Links clickable

✓ PERFORMANCE
  [ ] FCP < 2s on 4G
  [ ] LCP < 4s on 4G
  [ ] Memory < 60MB
  [ ] No jank on scroll
  [ ] No layout shift

✓ FERIA DEMO
  [ ] Can hand phone to investor
  [ ] They can tap through Pulso → Taty → Telegram
  [ ] All features visible and responsive
  [ ] Takes ~10 min to demo everything
```

---

## RESUMEN: HOY vs. DESPUÉS

### HOY (2026-05-24) — TESTING CON MOCK DATA

| Component | Data Source | Status |
|-----------|-------------|--------|
| **Pulso** | financial_snapshot (MOCK) | ✅ Testeable |
| **Centinela** | Rules engine (evaluates mock data) | ✅ Testeable |
| **Taty** | LLM + RAG (no datos reales necesarios) | ✅ Testeable |
| **Telegram** | LLM responses (no datos reales necesarios) | ✅ Testeable |
| **Mobile PWA** | UI/UX (responsive design) | ✅ Testeable |
| **DIAN** | ❌ No integrado | Mock rules solamente |
| **SIIGO** | ❌ No integrado | Mock financials solamente |
| **Sync Manager** | ❌ No integrado | Mock causalización solamente |

### DESPUÉS (Junio/Julio) — TESTING CON DATOS REALES

```
Cuando:
  ✓ SIIGO connector implementado
  ✓ DIAN API integration lista
  ✓ Sync Manager + Data Lake conectados

Cambios MÍNIMOS:
  - Cambiar data_source: "siigo" en lugar de "mock"
  - Same UI/UX (PulsoView.tsx no cambia)
  - Same API (GET /api/v1/pulso/dashboard/{company_id} igual)
  - Mismos endpoints, diferentes datos
```

---

## PLAN EJECUCIÓN: OPCIÓN C ULTRA-COMPLETO (HOY)

### Timeline: 3-4 horas

```
BLOQUE 1 (15 min): Auth → Dashboard
BLOQUE 2 (30 min): Taty Contadora
BLOQUE 3 (20 min): Centinela Rules (con mock data)
BLOQUE 4 (30 min): Pulso Dashboard ← AQUÍ USAS MOCK DATA
  ├─ Crear tabla financial_snapshot
  ├─ Seed mock data (Contexia, FEREZ, Importaciones)
  ├─ Implementar GET /api/v1/pulso/dashboard API
  ├─ Crear PulsoView.tsx component
  └─ Test con 3 companies (diferentes KPIs/risk levels)

BLOQUE 5 (10 min): Telegram Bot
BLOQUE 6 (10 min): Fiscal Tab
BLOQUE 7 (60 min): Mobile PWA ← CRÍTICO PARA FERIAS
  ├─ iOS: Install + fullscreen + Pulso + Taty
  ├─ Android: Install + fullscreen + Pulso + Taty
  ├─ Performance: FCP/LCP on 4G throttle
  └─ Demo: Pasar teléfono a "investor" (tu colega)
```

---

## ESPECIAL: CÓMO MOSTRAR EN FERIAS

### Demo Flow (10 minutos)

```
1. "Abre el app..." (launch iOS PWA from home screen)
2. "Esto es Contexia — un asistente fiscal IA"
3. Tap Pulso
   "Aquí ves tu estado fiscal: ingresos, utilidad, riesgo"
   Point: "Semáforo verde = compliant"
4. Tap Taty
   "Pregunta al asistente fiscal..."
   Ask: "¿Cuál es el límite de ingresos para Régimen Simple?"
   "Responde en < 4 segundos, cita las fuentes"
5. Tap Telegram section
   "También disponible por Telegram"
   "Misma IA, múltiples canales"
6. "Cuando conectemos SIIGO y DIAN, estos datos se actualizan automáticamente"
7. "¿Quieres probarlo?" (pass phone to investor)
```

**Lo que ven**:
- ✅ Professional app (iOS/Android, not web)
- ✅ Real features (Pulso, Taty, Alerts)
- ✅ Responsive design (works on phone)
- ✅ Fast response (Taty < 4s)
- ✅ Multi-channel (web + Telegram + mobile)
- ✅ Serious: mentions SIIGO/DIAN integration roadmap

---

## ARCHIVO DE IMPLEMENTACIÓN

Para empezar HOY, necesitas:

1. **SQL**: `financial_snapshot` table + seed data
2. **Backend**: `pulso_endpoints.py` con el GET endpoint
3. **Frontend**: `PulsoView.tsx` component
4. **Mobile**: Install PWA en iPhone/Android, test

¿Quieres que cree estos 3 archivos ahora con datos listos para ferias?

**Responde**:
- ✅ SÍ: Creo los archivos, copias a Supabase, ejecutas tests
- ❓ Preguntas primero: ¿Qué custom KPIs quieres? ¿Qué valores mock?
