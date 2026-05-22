# Contexia Backend - FastAPI

Este es el servidor API para Contexia, construido con FastAPI y conectado a Supabase.

## Estructura del Proyecto

- `core/`: Lógica central (seguridad, excepciones, constantes).
- `domain/`: Modelos de datos (Pydantic).
- `application/`: Servicios de lógica de negocio.
- `infrastructure/`: Implementaciones de persistencia (SQLAlchemy, Supabase).
- `presentation/`: Controladores API (Routers, Endpoints).

## Ejecución Local

1. Crear entorno virtual: `python -m venv venv`
2. Activar: `.\venv\Scripts\Activate`
3. Instalar: `pip install -r requirements.txt`
4. Configurar `.env` basándose en `.env.example`.
5. Ejecutar: `python main.py`

Acceder a la documentación en `http://localhost:8080/docs`.

## LLM Architecture (Cloud-Only)

Contexia usa una arquitectura **Cloud-Only** con failover automático para optimizar costos:

- **Tier 1 (Non-sensitive):** OpenRouter Free (FAQ, social media, general)
- **Tier 2 (Financial):** OpenRouter Free (Pulso analysis, Centinela monitoring)
- **Tier 3 (Critical):** Groq (Fiscal decisions, compliance audits)

**Failover chain:** `OpenRouter Free → Groq → Cerebras → Mistral → Gemini → OpenRouter`

**Key features:**
- ✅ Completely transparent to clients (no visible changes)
- ✅ Automatic fallback if OpenRouter is rate-limited
- ✅ Zero local dependencies (no Ollama, no LM Studio)
- ✅ Cost optimized: -54% margin improvement ($2.700/month savings)

**Files:**
- `core/model_selector.py` - Task → Model routing logic
- `agents/llm_engine.py` - Failover chain implementation
- `presentation/agents_endpoints.py` - REST endpoints using LLM
- `docs/DEVELOPMENT_STRATEGY.md` - Dev team guide (OpenRouter + Claude Opus)
- `CLOUD_ONLY_MIGRATION.md` - Complete migration documentation

See [Cloud-Only Migration Guide](CLOUD_ONLY_MIGRATION.md) for full details.
