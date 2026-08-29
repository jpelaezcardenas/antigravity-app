# OmniRoute — Infraestructura LLM para Contexia
**Fecha:** 2026-08-29
**Estado:** ACTIVO — piloto shadow-mode

---

## Arquitectura

```
Claude Code Desktop ─┐
                     ├──> OmniRoute (localhost:20128/v1)
Hermes Agentic OS ───┤             │
                     │             ├──> Combos por tarea
Backend Contexia ────┘             ├──> Fallback automático
                                   └──> Observabilidad
```

## Combos configurados

| Combo | Uso | Estrategia | Modelos |
|-------|-----|------------|---------|
| contexia-fast-free | Clasificación, FAQ, borradores | Prioridad | mimo-v2.5 → deepseek-v4 → big-pickle |
| contexia-docs-free | Extracción, JSON, documentos | Prioridad | deepseek-v4 → mimo-v2.5 → hy3 → big-pickle |
| contexia-tools-free | Tool calling, multi-step | Prioridad | mimo-v2.5 → nemotron-3 → deepseek-v4 |
| contexia-dev-free | Código, pruebas, documentación | Prioridad | deepseek-v4 → mimo-v2.5 → north-mini-code |
| contexia-private-local | Datos confidenciales | Prioridad local | mimo-v2.5 (local primero) |
| contexia-critical-review | Revisión supervisada | Prioridad | deepseek-v4 → mimo-v2.5 |

## API Keys separadas

| Key | Servicio | Permisos |
|-----|----------|----------|
| hermes-prod | Hermes Agentic OS | Solo inferencia |
| backend-prod | FastAPI Backend | Solo inferencia |
| n8n-prod | Automatizaciones | Solo inferencia |
| claude-code-dev | Desarrollo local | Solo inferencia |
| admin-omniroute | Administración | manage (no usar en apps) |

## Endpoints

- API: http://localhost:20128/v1
- Dashboard: http://localhost:20128
- Login: CHANGEME (cambiar)

## Mapeo de flujos a combos

```typescript
const AI_ROUTE = {
  leadClassification: "contexia-fast-free",
  customerSupportDraft: "contexia-fast-free",
  documentExtraction: "contexia-docs-free",
  agentTools: "contexia-tools-free",
  engineering: "contexia-dev-free",
  confidentialInternal: "contexia-private-local",
  complianceReview: "contexia-critical-review",
} as const;
```

## Piloto shadow-mode (7-14 días)

### Métricas a evaluar

| Métrica | Umbral |
|---------|--------|
| Disponibilidad tareas no críticas | ≥95% |
| JSON válido en extracción | ≥98% |
| Acierto de clasificación | ≥90% |
| Flujos con herramientas exitosos | ≥95% |
| Acciones críticas autónomas | 0% |
| Fugas de secretos/datos prohibidos | 0 |

### Evaluación por combo

- Éxito técnico: respuesta válida, sin timeout ni error
- Éxito funcional: JSON correcto, herramientas correctas
- Precisión del negocio: campos extraídos correctos
- Tasa de fallback: cuántas veces cambia de proveedor
- Latencia p50 y p95
- Tokens por tarea
- Incidentes por proveedor
- Porcentaje que necesita corrección humana

## Política de datos

| Clasificación | ¿Puede usar free routing? | Política |
|---------------|---------------------------|----------|
| PÚBLICO | Sí | Combo free |
| INTERNO | Sí, con validación | Combo free |
| CONFIDENCIAL | Solo con anonimización | contexia-private-local |
| RESTRINGIDO | No | Modelo local + aprobación humana |

## Seguridad

- No exponer puerto 20128 públicamente
- Usar VPN/Tailscale o proxy inverso con TLS
- REQUIRE_API_KEY=true en producción
- CORS_ORIGIN específico
- No enviar credenciales, RUTs completos, extractos bancarios a modelos remotos

## Decisiones clave

1. No renovar Mimo si piloto confirma métricas (7-14 días)
2. No usar "Best Free" genérico — usar combos por tarea
3. Validación determinista fuera del LLM para contabilidad
4. Trazabilidad por cliente, flujo, modelo, proveedor
5. Aprobación humana para decisiones tributarias

## Documentación relacionada

- Skill Hermes: contexia-omniroute
- GBrain: omniroute-setup-contexia
- Repo: docs/OMNIRROUTE_SETUP.md
- Plan: ~/.hermes/plans/omniroute-setup-complete.md
