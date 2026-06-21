# Configuración de Clientes Piloto - Taty Fiscal MVP

**Fecha:** 25 mayo 2026  
**Objetivo:** Definir mapeos company_id → NIT → agent_profile para Taty y Centinela

---

## 1. Clientes Confirmados

### A. Contexia
**Email:** jpelaezcardenas@gmail.com  
**NIT:** 9.867.082-4  
**Nombre Empresa:** Contexia  
**Plan:** Enterprise  
**Sector:** Servicios Digitales / Tecnología  
**Régimen:** Régimen Común  
**Configuración Taty:**
- Tono: Profesional + accesible, orientado a founders y CFOs
- Restricciones: Responde sobre NIIF, Renta, IVA, Régimen, Retenciones, Provisiones
- Fuentes habilitadas: Normograma DIAN, Estatuto Tributario, Guías DIAN, Docs Contexia
- Escalamiento: `requires_human_review = True` si pregunta sobre planificación fiscal específica

### B. FEREZ SAS
**Email:** fperez@ferez.co  
**NIT:** 900.123.456-7  
**Nombre Empresa:** FEREZ SAS  
**Plan:** Enterprise  
**Sector:** Comercio / Importaciones (investigar)  
**Régimen:** Régimen Común  
**Configuración Taty:**
- Tono: Corporativo y preciso
- Restricciones: Según sector (importaciones → régimen especial, retenciones, IVA)
- Fuentes: Normograma + Resoluciones sobre comercio exterior + documentos FEREZ (si existen)
- Escalamiento: Alto (operaciones internacionales requieren validación)

### C. Importaciones Martinez
**Email:** carlos@importacionesmtz.co  
**NIT:** 800.456.789-0  
**Nombre Empresa:** Importaciones Martinez  
**Plan:** Growth  
**Sector:** Comercio / Importaciones  
**Régimen:** Régimen Común  
**Configuración Taty:**
- Tono: Accesible, pequeña/mediana empresa
- Restricciones: Preguntas sobre IVA, Renta, Retenciones, Facturación electrónica
- Fuentes: Normograma básico + Guías DIAN para PYME
- Escalamiento: Moderado  

---

## 2. Mapeo Telegram → Company ID

**Tabla: `telegram_chat_mappings`** (Nueva, para MVP)

| telegram_chat_id | company_id | nit | empresa | active |
|------------------|------------|-----|--------|--------|
| `-1001234567890` | `ctx-001` | `900-123-456-7` | Contexia | true |
| `[chat_id_ferez]` | `ferez-001` | `[nit_ferez]` | Férez | true |
| `[chat_id_otro]` | `other-001` | `[nit_otro]` | Otro Cliente | true |

**Cómo obtener telegram_chat_id:**
1. Agregar bot `@taty_contexia_bot` a grupo o chat privado
2. Enviar mensaje `/start`
3. Revisar logs: `print(update.message.chat_id)` o webhook logs
4. Insertar en `telegram_chat_mappings`

---

## 3. Seed Data: `agent_profiles`

```sql
INSERT INTO agent_profiles (company_id, nit, empresa_nombre, sector, regimen, tono, fuentes_habilitadas, restricciones, escalamiento_criterios, created_at)
VALUES
  (
    'ctx-001',
    '900-123-456-7',
    'Contexia',
    'Servicios Digitales',
    'Régimen Común',
    'Profesional y accesible, orientado a founders y CFOs',
    'Normograma DIAN, Estatuto Tributario, Guías DIAN, Documentos Contexia',
    'Responder sobre: NIIF, Renta, IVA, Régimen, Retenciones, Provisiones, CxC/CxP, Liquidez',
    'requires_human_review si: planificación fiscal específica, interpretación legal, cambio de régimen, situaciones no estandarizadas',
    NOW()
  );
```

---

## 4. Investigación Pendiente

**Acciones para mañana (T1):**

- [ ] Buscar NIT y sector de **Férez** (¿en Supabase clients table? ¿email al usuario?)
- [ ] Buscar NIT y sector del **cliente adicional** (¿es un cliente beta de Contexia? ¿ficticio?)
- [ ] Obtener `telegram_chat_id` del grupo/chat privado donde agregar bot
- [ ] Confirmar NITs con usuario si son reales (compliance: datos sensibles)

**Comando para buscar en Supabase (si hay datos legacy):**
```sql
SELECT company_id, nit, name, sector FROM clients 
WHERE active = true 
LIMIT 10;
```

---

## 5. Notas de Seguridad

- **NITs son datos sensibles**: No commitear a git real; usar `.env` o tabla Supabase con RLS
- **Telegram chat_ids**: Pueden cambiar si el bot es removido/readd; validar en runtime
- **Configuraciones por cliente**: Agent profiles deben viajar en request o fetcharse de DB en cada llamada

---

## 6. Próximas Fases (Fuera de MVP)

- Onboarding UI para nuevos clientes (crear agent_profile sin SQL)
- Webhook de Telegram en cliente (grupo/chat privado auto-resuelto)
- Persistencia de conversation_id por cliente (continuidad multi-turno)
- Personalización de restricciones por sector (templates)
