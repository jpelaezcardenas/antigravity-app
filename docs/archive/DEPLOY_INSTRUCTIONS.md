# Guía de Despliegue - Contexia Full Stack

Esta guía detalla los pasos para desplegar la arquitectura completa de Contexia: Landing Page, Dashboard React, Backend FastAPI y Supabase.

## 1. Base de Datos (Supabase)
1.  **Proyecto**: Crea un proyecto en [Supabase](https://supabase.com/).
2.  **Esquema**: Ve al **SQL Editor** y ejecuta el contenido de [supabase_schema.sql](file:///c:/Users/jpela/Projects/Contexia/supabase_schema.sql).
3.  **Configuración**: En **Project Settings > API**, obtén la URL y la Anon Key.

## 2. Backend (FastAPI en Railway)
1.  **Repositorio**: Conecta tu repositorio de GitHub a [Railway](https://railway.app/).
2.  **Root Directory**: Selecciona la carpeta `apps/backend/`.
3.  **Variables de Entorno**:
    - `DATABASE_URL`: URL de conexión de Supabase (Postgres).
    - `SUPABASE_URL`: Tu URL de proyecto Supabase.
    - `SUPABASE_KEY`: Tu Anon Key de Supabase.
    - `JWT_SECRET`: Una cadena aleatoria larga para firmar tokens.
    - `JWT_ALGORITHM`: `HS256`.
4.  **Dominio**: Configura el dominio personalizado `api.contexia.online` en Railway.

## 3. Dashboard React (Vercel)
1.  **Proyecto**: Conecta el repositorio a [Vercel](https://vercel.com/).
2.  **Configuración de Build**:
    - **Framework Preset**: Vite.
    - **Root Directory**: `Contexia_Daschboard/`.
    - **Build Command**: `npm install && npm run build`.
    - **Output Directory**: `dist` (Nota: Luego movemos esto a la carpeta `app/` del repo raíz si queremos servirlo desde allí, o configuramos Vercel para que el proyecto del dashboard sea independiente).
3.  **Variables de Entorno**:
    - `VITE_API_URL`: `https://api.contexia.online/api/v1`.
4.  **Integración con Landing**: El archivo `vercel.json` en la raíz del repositorio se encarga de que `contexia.online/app` cargue el dashboard. Asegúrate de que el build del dashboard se despliegue en la subcarpeta `app/` del proyecto principal.

## 4. Landing Page (Vercel)
1.  **Proyecto**: El proyecto principal en Vercel debe apuntar a la raíz del repositorio.
2.  **Dominios**: Configura `contexia.online` como dominio principal.
3.  **Redirecciones**: `vercel.json` redirige la raíz a `landing.html` y mantiene `/app` para el dashboard.

---
### Notas Importantes
- **Usuarios de Prueba**: Los usuarios definidos en el script SQL (`lavaderos_ld@contexia.com`, `sion@contexia.com`, `repuestos_don_alvaro@contexia.com`) funcionan con la contraseña `demo` gracias al bypass de desarrollo en el backend.
- **SSL**: Railway y Vercel gestionan automáticamente los certificados SSL.
