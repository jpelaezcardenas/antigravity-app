# Configuración de Supabase para Contexia

Sigue estos pasos para configurar la base de datos de Contexia:

1.  **Crea un proyecto en Supabase**: Ve a [supabase.com](https://supabase.com/) y crea un nuevo proyecto llamado `Contexia`.
2.  **Ejecuta el Script SQL**:
    *   En el panel lateral izquierdo, ve a **SQL Editor**.
    *   Haz clic en **New query**.
    *   Copia y pega el contenido del archivo `supabase_schema.sql` que se encuentra en la raíz del repositorio.
    *   Haz clic en **Run**.
3.  **Configura las Variables de Entorno**:
    *   Ve a **Project Settings** > **API**.
    *   Copia la `Project URL` y la `anon key`.
    *   En tu entorno de desarrollo o servidor de backend, configura las variables `SUPABASE_URL` y `SUPABASE_KEY`.
4.  **Autenticación**:
    *   Ve a **Authentication** > **Users**.
    *   Asegúrate de que los usuarios de prueba existan o créalos manualmente.
    *   Nota: Para la demo del backend, se ha implementado un bypass que acepta la contraseña `demo` para los correos especificados en el código.

## Estructura de Tablas
- `usuarios`: Datos maestros de la empresa y planes.
- `transacciones`: Historial financiero sincronizado.
- `alertas_fiscales`: Alertas del sistema "Centinela".
- `facturas_vencidas`: Cartera para el "Asistente de Cobro".
- `eventos_cobro`: Log de acciones realizadas por el usuario.
