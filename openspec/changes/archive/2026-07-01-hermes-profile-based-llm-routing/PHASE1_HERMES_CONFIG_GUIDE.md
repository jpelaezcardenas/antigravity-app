# Phase 1: Hermes Dashboard Configuration Guide

**Change ID:** hermes-profile-based-llm-routing  
**Phase:** 1 (Manual Hermes Setup)  
**Duration:** ~30-45 minutes  
**Difficulty:** Easy (mostly clicking in UI)

---

## Overview

El backend en antigravity-app YA ESTÁ DEPLOYADO y listo. Ahora necesitas configurar **Hermes Dashboard** para:

1. **Registrar modelos** (GLM 5.2, Phi, Gemma)
2. **Crear 8 profiles** con modelos + fallback chains
3. **Configurar API Gateway** para inyectar headers de profile

Después, antigravity-app automaticamente usará los profiles.

---

## Step 0: Abrir Hermes Dashboard

```
URL: http://localhost:9119
```

Deberías ver esto:

```
┌──────────────────────────────────┐
│  Hermes Agent - Dashboard        │
├──────────────────────────────────┤
│ MODELS | PROFILES | OPERATIONS   │
│ JOBS | API GATEWAY | SKILLS      │
└──────────────────────────────────┘
```

Si no carga, verifica que Hermes está corriendo:
```bash
curl http://localhost:9119/health
# Esperado: HTML response (página de Hermes)
```

---

## Step 1: Registrar Modelos en Hermes

### 1.1 Ir a MODELS Tab

```
Click: MODELS tab en la navegación superior
```

Deberías ver la lista de modelos disponibles.

### 1.2 Registrar GLM 5.2

**Si GLM 5.2 ya aparece en la lista:** Skip a Step 1.3

**Si NO aparece:**

```
1. Click: "+ Add Model" (botón en esquina superior derecha)
2. Nombre: glm-5.2
3. Provider: GLM (Z.AI)
4. API Key: Tu GLM_API_KEY (ya configurada en .env)
5. Click: Save
```

**Expected result:**
```
✅ glm-5.2 registered (GLM / Z.AI)
```

### 1.3 Registrar Phi:latest (Local)

```
1. Click: "+ Add Model"
2. Nombre: phi:latest
3. Provider: Ollama (local)
4. Endpoint: http://localhost:11434
5. Model name in Ollama: phi:latest
6. Click: Save
```

**Expected result:**
```
✅ phi:latest registered (Ollama / localhost:11434)
```

### 1.4 Registrar Gemma 3 2B (Local)

```
1. Click: "+ Add Model"
2. Nombre: gemma:2b
3. Provider: Ollama (local)
4. Endpoint: http://localhost:11434
5. Model name in Ollama: gemma:2b
6. Click: Save
```

**Expected result:**
```
✅ gemma:2b registered (Ollama / localhost:11434)
```

### Result: Models Registered

Deberías ver en el MODELS tab:

| Model | Provider | Status |
|-------|----------|--------|
| glm-5.2 | GLM | ✅ Ready |
| phi:latest | Ollama | ✅ Ready |
| gemma:2b | Ollama | ✅ Ready |

---

## Step 2: Crear 8 Profiles

### 2.0 Ir a PROFILES Tab

```
Click: PROFILES tab en la navegación superior
```

Deberías ver:
```
Existing Profiles:
- default (glm-5.2)
- contexia (glm-5.2)

New Profiles to Create: 8
```

### 2.1 Crear PROFILE: taty-v1

```
Click: "+ Create Profile" o "+ New"
```

**Formulario:**

```
Profile Name: taty-v1
Display Name: Taty Fiscal Advisor
Description: Interactive fiscal advice using GLM 5.2
Primary Model: glm-5.2
Fallback Models: 
  1. groq (if available)
  2. openrouter (if available)

Temperature: 0.3 (bajo = más preciso para fiscal)
Max Tokens: 2000

Click: Save Profile
```

**Expected:**
```
✅ Profile "taty-v1" created
  Primary: glm-5.2
  Fallbacks: [groq, openrouter]
```

### 2.2-2.8 Crear Remaining Profiles

**Patrón:** Mismo proceso, cambiar nombre + descripción + modelo

#### **2.2 centinela-v1**
```
Name: centinela-v1
Display: Centinela Monitoring
Primary Model: phi:latest
Fallback: [groq, openrouter_free]
Temperature: 0.5
Description: Financial monitoring — batch processing
```

#### **2.3 pulso-v1**
```
Name: pulso-v1
Display: Pulso Daily Report
Primary Model: phi:latest
Fallback: [groq, openrouter_free]
Temperature: 0.4
Description: Nightly cash flow summary
```

#### **2.4 radar-v1**
```
Name: radar-v1
Display: Radar Predictive
Primary Model: glm-5.2
Fallback: [groq, cerebras]
Temperature: 0.2 (bajo = preciso para predicciones)
Description: Predictive financial risk analysis
```

#### **2.5 auditoria-v1**
```
Name: auditoria-v1
Display: Auditoría Sombra
Primary Model: glm-5.2
Fallback: [groq, cerebras]
Temperature: 0.1 (muy bajo = máxima precisión)
Description: Compliance & regulatory audit
```

#### **2.6 social-ops-v1**
```
Name: social-ops-v1
Display: Social Operations
Primary Model: gemma:2b
Fallback: [groq, openrouter_free]
Temperature: 0.8 (alto = creativo para contenido)
Description: Social media content generation
```

#### **2.7 kb-v1**
```
Name: kb-v1
Display: Knowledge Base RAG
Primary Model: gemma:2b
Fallback: [groq, openrouter_free]
Temperature: 0.5
Description: Knowledge base retrieval & formatting
```

#### **2.8 maestro-v1**
```
Name: maestro-v1
Display: Maestro Orchestrator
Primary Model: glm-5.2
Fallback: [groq, cerebras, openrouter]
Temperature: 0.3 (bajo = coordinación precisa)
Description: Multi-agent orchestration
```

### Result: 8 Profiles Created

En PROFILES tab deberías ver:

```
✅ taty-v1 (glm-5.2)
✅ centinela-v1 (phi:latest)
✅ pulso-v1 (phi:latest)
✅ radar-v1 (glm-5.2)
✅ auditoria-v1 (glm-5.2)
✅ social-ops-v1 (gemma:2b)
✅ kb-v1 (gemma:2b)
✅ maestro-v1 (glm-5.2)
```

---

## Step 3: Configurar API Gateway

### 3.1 Ir a API GATEWAY o GATEWAY Tab

```
Click: API GATEWAY tab (o similar, depende versión Hermes)
```

### 3.2 Enable Gateway

```
Toggle: "Enable API Gateway" → ON
Port: 8642 (default)
```

### 3.3 Configurar Backend

```
Backend URL: http://localhost:8000
(Este es antigravity-app en local, o Railway URL en production)

Si estás en PRODUCTION:
Backend URL: https://antigravity-app-production-175a.up.railway.app
```

### 3.4 Configurar Header Injection (Si Disponible)

**Si Hermes tiene opción de "Header Injection":**

```
Nombre del Header: X-Hermes-Profile
Valor: Tomar del: PROFILE SELECTION (automático)
```

**Si NO tiene esta opción:**
- Hermes puede inyectar automáticamente basado en profile activo
- O antigravity-app puede leer del contexto de Hermes

Skip para ahora, vamos a testear en Step 4.

### 3.5 Guardar Configuración

```
Click: Save Gateway Configuration
```

**Expected:**
```
✅ API Gateway enabled on port 8642
✅ Backend: http://localhost:8000 (or Railway URL)
✅ Ready to route requests
```

---

## Step 4: Testear Configuration

### 4.1 Verificar Health Check

```bash
# Test: Health check SIN profile header
curl http://localhost:8642/api/v1/health

# Expected: 200 OK (antigravity-app responde)
```

### 4.2 Testear con Profile Header

**Opción A: Con curl (si curl está disponible)**

```bash
# Test: Taty agent CON profile header
curl -X POST http://localhost:8642/api/v1/agents/ask \
  -H "X-Hermes-Profile: taty-v1" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the UVT for 2026?"}'

# Expected: Response from antigravity-app usando taty-v1 profile
# Latency: ~1-2 segundos
```

**Opción B: Via Hermes Dashboard (si hay UI para test)**

```
1. Click: una de las tabs de "OPERATIONS" o "Test"
2. Selecciona Profile: taty-v1
3. Click: Test Request
4. Pregunta: "What is the UVT for 2026?"
5. Click: Send
```

### 4.3 Verificar Logs

**En antigravity-app logs deberías ver:**

```
[19:46:12] Using profile 'taty-v1' with fallback chain: [groq, openrouter, cerebras]
[19:46:12] Attempting LLM request via groq
[19:46:13] [OK] Success with groq
[19:46:13] Response sent (1247ms)
```

Si ves esto: ✅ **Phase 1 está COMPLETO**

---

## Step 5: Entender el Flujo

### Cómo funciona después de Phase 1:

```
1. Cliente hace request a Hermes Gateway (puerto 8642)
   POST /api/v1/agents/ask

2. Usuario selecciona Profile en Hermes Dashboard: "taty-v1"

3. Hermes Gateway inyecta header:
   X-Hermes-Profile: taty-v1

4. antigravity-app recibe request con header

5. LLM Engine: "Tengo profile 'taty-v1'"
   → Busca en PROFILE_CONFIGS
   → Encuentra: primary=glm-5.2, fallback=[groq, openrouter, cerebras]

6. Intenta llamar a Groq
   → Si funciona: responde ✅
   → Si falla: intenta siguiente (openrouter)
   → Si TODO falla: error

7. Respuesta se envía al cliente
   Logs registran: profile_name, provider_usado, latencia, costo
```

---

## Troubleshooting

### Problema: "Gateway no responde en puerto 8642"

**Solución:**

```bash
# Verificar que Hermes está corriendo
curl http://localhost:9119/health

# Si responde: Gateway debería estar en 8642
curl http://localhost:8642/health
```

Si NO responde:
```bash
# Reinicia Hermes
hermes gateway restart

# O:
pkill -f "hermes" && sleep 2 && hermes dashboard
```

### Problema: "API Gateway retorna 404"

**Solución:**

1. Verifica que antigravity-app está corriendo (puerto 8000 o Railway URL)
2. Verifica que Backend URL en Gateway está correcta
3. Reinicia Gateway:
   ```bash
   hermes gateway restart
   ```

### Problema: "Profile header not being injected"

**Solución:**

1. Si Hermes no auto-inyecta header:
   - Manualmente añade header en test: `-H "X-Hermes-Profile: taty-v1"`
   
2. Verifica que antigravity-app está recibiendo el header:
   - Chequea logs de antigravity-app
   - Debería mostrar: "Using profile 'taty-v1'"

### Problema: "Ollama model not found (Phi timeout)"

**Solución:**

```bash
# Verifica que modelo existe
ollama list

# Si phi:latest no está:
ollama pull phi:latest

# Reinicia Hermes
hermes gateway restart
```

---

## Checkpoint: Phase 1 Complete

Cuando veas TODO esto, Phase 1 está DONE:

- [ ] ✅ Hermes Dashboard abre en http://localhost:9119
- [ ] ✅ 3 modelos registrados (glm-5.2, phi:latest, gemma:2b)
- [ ] ✅ 8 profiles creados en PROFILES tab
- [ ] ✅ API Gateway enabled en puerto 8642
- [ ] ✅ Backend URL apunta a http://localhost:8000
- [ ] ✅ Health check responde en 8642
- [ ] ✅ Test con profile header funciona
- [ ] ✅ antigravity-app logs muestran "Using profile 'xxx'"

**Si TODO está checked:** Phase 1 COMPLETO ✅

---

## Next: Phase 2 (Opcional, Ya Hecho)

Si quieres verificar que antigravity-app YA está usando profiles:

```bash
# Opcional: Ver código que usa profiles
cat apps/backend/agents/llm_engine.py | grep "PROFILE_CONFIGS"

# Opcional: Correr tests
pytest apps/backend/tests/test_profile_support.py -v
```

---

## Reference: Profile Summary

| Profile | Model | Fallback | Use Case |
|---------|-------|----------|----------|
| **taty-v1** | glm-5.2 | [groq, openrouter, cerebras] | Fiscal advice |
| **centinela-v1** | phi:latest | [groq, openrouter_free] | Monitoring |
| **pulso-v1** | phi:latest | [groq, openrouter_free] | Nightly batch |
| **radar-v1** | glm-5.2 | [groq, cerebras, openrouter] | Predictions |
| **auditoria-v1** | glm-5.2 | [groq, cerebras] | Compliance |
| **social-ops-v1** | gemma:2b | [groq, openrouter_free] | Content |
| **kb-v1** | gemma:2b | [groq, openrouter_free] | RAG |
| **maestro-v1** | glm-5.2 | [groq, cerebras, openrouter] | Orchestration |

---

## Questions?

Si algo no funciona o tienes dudas:

1. **Verifica logs:** antigravity-app y Hermes
2. **Chequea connectivity:** `curl localhost:8642/health`
3. **Reinicia Hermes:** `hermes gateway restart`
4. **Revisa configuración:** Backend URL correcta, profiles creados

---

**Estimated Time:** 30-45 minutos  
**Difficulty:** ⭐⭐ (mostly clicking)  
**Result:** Hermes Dashboard configured, antigravity-app routing via profiles ✅
