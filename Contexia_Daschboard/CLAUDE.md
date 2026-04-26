# Contexia - Guía de Proyecto

## Visión del Negocio
Contexia es una **Entidad B tecnológica** (no una firma contable tradicional). Actúa como un **GPS de Flujo de Caja y Riesgo Fiscal** para PyMEs en Colombia.

## Arquitectura Técnica
- **Frontend:** React + Vite + Tailwind CSS.
- **Estilo:** Premium (Glassmorphism, Dark Mode, Orbitron/Rajdhani typography).
- **Backend Primario:** Supabase (Auth, DB, Realtime).
- **Lógica de Automatización:** (Planificado) Python/FastAPI para OCR, integración XML DIAN y SyncManager.
- **Despliegue:** 
  - Landing: `contexia.online`
  - Web App: `app.contexia.online`
  - API: `api.contexia.online`

## Reglas de Desarrollo
1. **Multi-tenant:** Todo registro debe estar vinculado a un `company_id`.
2. **Seguridad:** Usar Row Level Security (RLS) en Postgres. No exponer lógica de negocio sensible en el cliente.
3. **Estética:** Mantener el estándar premium (Teal #2DD4BF, Violet #8B5CF6, Navy #0F172A).
4. **Validación:** El XML de la DIAN es la fuente de verdad documental.
5. **No Secretos:** Nunca subir llaves de API al repositorio. Usar variables de entorno (`.env`).

## Comandos Frecuentes
- `npm run dev`: Iniciar entorno de desarrollo.
- `npm run build`: Generar bundle de producción.
- `supabase gen types typescript --project-id wzqymuzpjbagnbgsiqig > src/types/supabase.ts`: Actualizar tipos de base de datos.
