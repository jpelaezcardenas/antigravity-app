# Guía de Despliegue - Contexia

Sigue estos pasos para poner la plataforma en producción.

## 1. Supabase (Base de Datos)
1. Crea un proyecto en Supabase.
2. Ejecuta el SQL de `apps/backend/supabase_schema.sql`.
3. Copia las llaves API y el string de conexión.

## 2. Backend (FastAPI en Railway)
1. Sube la carpeta `apps/backend/` a un nuevo servicio en Railway.
2. Configura las Variables de Entorno:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `DATABASE_URL`
   - `JWT_SECRET`
3. Railway detectará el `Dockerfile` y desplegará automáticamente en el puerto 8080.
4. (Opcional) Configura dominio `api.contexia.online`.

## 3. Dashboard (React en Vercel)
1. Conecta el repositorio a Vercel.
2. Configura la "Root Directory" como `Contexia_Daschboard`.
3. Agrega variables de entorno:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL=https://api.contexia.online/api/v1`
4. Despliega y configura el dominio `app.contexia.online`.

## 4. Landing Page (Raíz en Vercel)
1. Conecta el repositorio a Vercel.
2. Configura la "Root Directory" como la raíz del proyecto.
3. El archivo `vercel.json` ya está configurado para redirecciones.
4. Configura el dominio principal `contexia.online`.

---
*Desarrollado por el equipo de Advanced Agentic Coding de Google Deepmind.*
