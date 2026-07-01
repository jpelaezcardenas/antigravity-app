# 📚 API Reference — Contexia Agentes (v2.0)

**Generated:** 2026-06-21  
**Base URL:** `https://antigravity-app-production-175a.up.railway.app/api/v1`  
**Auth:** Bearer token (Supabase JWT)  
**Response Format:** JSON

---

## 1. CENTINELA FISCAL (`/centinela`)

### GET /centinela
List recent anomalies detected

**Response:**
```json
{
  "anomalies": [
    {
      "id": "anom-001",
      "type": "dian_siigo_mismatch",
      "dian_invoice_id": "CUFE-12345",
      "dian_amount": 10000000,
      "erp_amount": 0,
      "discrepancy": 10000000,
      "detected_at": "2026-06-21T10:30:00Z",
      "severity": "high",
      "status": "pending_resolution"
    }
  ],
  "total_pending": 1
}
```

### POST /centinela/resolve
Generate tax correction draft

**Request:**
```json
{
  "anomaly_id": "anom-001",
  "resolution_type": "generate_asiento"
}
```

**Response:**
```json
{
  "draft_id": "draft-001",
  "draft_type": "tax_correction",
  "lines": [
    {"account": "1105", "debit": 10000000, "credit": 0},
    {"account": "4105", "debit": 0, "credit": 10000000}
  ],
  "status": "pending_approval",
  "created_at": "2026-06-21T10:31:00Z"
}
```

---

## 2. PULSO DIARIO (`/pulso`)

### GET /pulso
Daily operational summary

**Query Params:**
- `date` (optional): YYYY-MM-DD, default=today
- `include_narrative` (optional): boolean, default=true

**Response:**
```json
{
  "date": "2026-06-21",
  "caja_disponible": {
    "total": 2450000,
    "cuenta_01": 1500000,
    "cuenta_02": 950000,
    "currency": "COP"
  },
  "vencimientos_hoy": [
    {
      "obligacion": "DIAN (IVA)",
      "dias_falta": 5,
      "monto": 500000,
      "prioridad": "high"
    }
  ],
  "variaciones_detectadas": [
    {
      "cuenta": "Caja",
      "variacion": -500000,
      "causa": "Pago a proveedores"
    }
  ],
  "narrative_summary": "Caja bajó $500K hoy principalmente por pago a proveedores. 1 vencimiento DIAN próximo (5 días). Sin alertas críticas."
}
```

---

## 3. RADAR PREDICTIVO (`/radar`)

### GET /radar
Risk analysis & forecasting

**Query Params:**
- `days_ahead` (optional): 30, 60, 90; default=30

**Response:**
```json
{
  "risk_level": "medium",
  "risk_score": 65,
  "risk_scenarios": [
    {
      "scenario": "Cashflow stress if customer XYZ doesn't pay",
      "probability": 0.35,
      "impact_cashflow": -2000000,
      "recommended_action": "Renegotiate payment terms"
    }
  ],
  "projected_cashflow": {
    "current": 2450000,
    "day_30": 1800000,
    "day_60": 1200000,
    "day_90": 500000,
    "critical_threshold": 300000
  },
  "anomaly_flags": [
    {
      "type": "client_late_payment",
      "client": "XYZ Corp",
      "days_overdue": 120,
      "confidence": 0.92
    }
  ]
}
```

---

## 4. AUDITORÍA SOMBRA (`/wizard/auditoria-sombra`)

### POST /wizard/auditoria-sombra
Generate continuous audit report

**Request:**
```json
{
  "period": "2026-06",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "report_id": "audit-2026-06",
  "status": "completed",
  "findings_count": 5,
  "pdf_url": "https://supabase.../audit-2026-06.pdf",
  "email_sent_to": ["auditor@contexia.com"],
  "findings": [
    {
      "id": "f1",
      "severity": "medium",
      "description": "5 transactions misclassified",
      "evidence": ["txn-001", "txn-002", "txn-003", "txn-004", "txn-005"],
      "recommendation": "Reclassify and post correcting entries"
    }
  ]
}
```

---

## 5. TATY (`/agents`)

### POST /agents
Send conversational message to Taty

**Request:**
```json
{
  "role": "taty",
  "message": "¿Cuánta caja tengo hoy?",
  "context": {
    "user_id": "user-001",
    "channel": "telegram"
  }
}
```

**Response:**
```json
{
  "response": "Según Pulso, tu caja disponible hoy es $2.45M. El desglose: Cuenta Operacional $1.5M, Fondo Rotatorio $950K.",
  "actions": [
    {
      "type": "link",
      "label": "Ver Pulso Completo",
      "url": "https://hermes.contexia.online/pulso"
    }
  ],
  "requires_approval": false
}
```

---

## 6. SOCIAL OPS (`/social-ops/*`)

### 6a. Content Ideas

#### GET /social-ops/ideas
List ideas in pipeline

**Response:**
```json
{
  "ideas": [
    {
      "id": "idea-001",
      "title": "5 tax tips for SMEs",
      "pillar": "education",
      "status": "draft",
      "created_at": "2026-06-20"
    }
  ]
}
```

#### POST /ideas/{id}/generate-draft
Generate content draft from idea

**Response:**
```json
{
  "draft_id": "draft-social-001",
  "type": "social_content_draft",
  "content": "Did you know? 💡 ...",
  "status": "pending_approval",
  "tone_validation": "SOUL.md compliant"
}
```

### 6b. Lead Reply Drafter

#### POST /social-ops/leads/reply-draft
Generate reply to inbound lead

**Request:**
```json
{
  "inbound_message": "Hola, ¿qué servicios ofrecen?",
  "client_profile": {"name": "Juan", "company": "ABC Inc"}
}
```

**Response:**
```json
{
  "draft_id": "draft-reply-001",
  "reply_text": "Hola Juan, ofrecemos...",
  "status": "pending_approval",
  "tone": "professional"
}
```

### 6c. Sales Closure Drafter

#### POST /social-ops/leads/sales-draft
Generate personalized sales offer

**Request:**
```json
{
  "lead_id": "lead-001",
  "lead_score": 85
}
```

**Response:**
```json
{
  "draft_id": "draft-sales-001",
  "offer": "Special package for your business...",
  "roi_calculation": {"annual_savings": 5000000, "payback_months": 6},
  "status": "pending_approval"
}
```

### 6d. Metrics

#### GET /social-ops/metrics
Pipeline health analytics

**Response:**
```json
{
  "pipeline": {
    "awareness": 50,
    "interest": 20,
    "decision": 5
  },
  "conversion_rate": 0.10,
  "anomalies": [
    {
      "type": "leads_stuck",
      "count": 3,
      "days_stuck": 90
    }
  ]
}
```

---

## 7. KNOWLEDGE BASE (`/kb`)

### GET /kb/search-similar
Vector similarity search

**Request:**
```json
{
  "query_embedding": [0.1, 0.2, ...], // 1536 dimensions
  "limit": 5,
  "threshold": 0.7
}
```

**Response:**
```json
{
  "matches": [
    {
      "id": "kb-001",
      "content": "Reclasificación por variación TCR",
      "similarity": 0.85,
      "approved_by": "contador@contexia.com",
      "timestamp": "2026-05-15T09:00:00Z",
      "confidence": 0.92
    }
  ]
}
```

---

## 8. MAESTRO ORCHESTRATOR (`/hermes/swarm`)

### POST /hermes/swarm/invoke
Invoke swarm orchestration

**Request:**
```json
{
  "action": "status",
  "agents": ["centinela", "pulso", "radar"],
  "parallel": true
}
```

**Response:**
```json
{
  "status": "completed",
  "execution_time_ms": 420,
  "results": {
    "centinela": {"pending_anomalies": 1},
    "pulso": {"caja_disponible": 2450000},
    "radar": {"risk_level": "medium"}
  },
  "narrative": "Status: 1 anomalía pendiente en Centinela, caja OK, riesgo moderado."
}
```

---

## 9. APPROVAL QUEUE (`/approval-queue`)

### GET /approval-queue
List pending approvals

**Response:**
```json
{
  "pending_drafts": [
    {
      "id": "draft-001",
      "type": "tax_correction",
      "payload_preview": "Asiento de ajuste...",
      "created_by": "centinela",
      "created_at": "2026-06-21T10:31:00Z",
      "priority": "high"
    }
  ],
  "total": 1
}
```

### POST /approval-queue/approve
Approve a draft

**Request:**
```json
{
  "draft_id": "draft-001",
  "reason": "Contexia's own invoice, matches DIAN",
  "approved_by": "contador@contexia.com"
}
```

**Response:**
```json
{
  "status": "approved",
  "draft_id": "draft-001",
  "execution_status": "pending",
  "vectorization_status": "in_progress",
  "timestamp": "2026-06-21T11:00:00Z"
}
```

### POST /approval-queue/reject
Reject a draft

**Request:**
```json
{
  "draft_id": "draft-001",
  "reason": "Information incomplete",
  "rejected_by": "contador@contexia.com"
}
```

**Response:**
```json
{
  "status": "rejected",
  "draft_id": "draft-001",
  "timestamp": "2026-06-21T11:05:00Z"
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Invalid input: missing required field 'amount'",
  "details": {...},
  "timestamp": "2026-06-21T11:06:00Z"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request payload
- `AUTHORIZATION_ERROR`: Missing/invalid auth token
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Rate Limits
- 1000 requests / min per user
- 100 requests / min for /kb/search-similar (vector DB intensive)
- Burst: up to 500 tokens per second

---

## Webhooks (Hermes → Agents)

### DIAN Invoice Received
```
POST /webhooks/dian
Body: { cufe, nit, amount, date }
```

### Approval Executed
```
POST /webhooks/approval-executed
Body: { draft_id, status, executed_at }
```

---

**Last updated:** 2026-06-21  
**Document source:** AGENTES.md + API_REFERENCE.md  
**Status:** FASE 3 complete, ready for FASE 4 implementation
