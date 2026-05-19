# Runbook: Conexión del Content OS con la Meta Graph API (Producción)

Este documento detalla el paso a paso exacto para pasar de la publicación **semiautomática asistida** (MVP) a la **publicación 100% automática** en tu Fan Page de Facebook de Contexia utilizando la API de Graph de Meta y n8n.

---

## Concepto Clave: El Token de Acceso de Página Perpetuo

Para que n8n pueda publicar en tu nombre a cualquier hora sin pedirte contraseña, necesitamos un **Page Access Token de larga duración (que nunca expira)**. 

Sigue estos 4 pasos simplificados para obtenerlo:

### Paso 1: Crear una App en Meta Developers
1. Ve al portal de [Meta for Developers](https://developers.facebook.com/) e inicia sesión con tu cuenta personal de Facebook.
2. Haz clic en **Mis aplicaciones** ➔ **Crear aplicación**.
3. Selecciona el tipo de aplicación: **Negocios (Business)** (esto te dará acceso directo a las APIs de Facebook Pages).
4. Dale un nombre descriptivo, por ejemplo: `Contexia Content Engine`, y completa el flujo de creación.

---

### Paso 2: Obtener los Permisos Iniciales en el Graph API Explorer
1. Entra a la herramienta [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. En la barra lateral derecha:
   * **Meta App:** Selecciona `Contexia Content Engine`.
   * **User or Page:** Selecciona tu **Fan Page de Contexia**.
3. En la sección de **Permissions**, añade obligatoriamente estos 3 permisos indispensables:
   * `pages_manage_posts` (para poder crear posts en la página).
   * `pages_read_engagement` (para leer los likes y comentarios de los posts en la fase de análisis).
   * `pages_show_list` (para poder listar tus páginas vinculadas).
4. Haz clic en **Generate Access Token**. Te abrirá un popup de Facebook preguntándote a qué página quieres darle acceso. Elige tu página de Contexia y confirma.

*¡Listo! Tienes un Token Temporal (expira en 1 hora).* Ahora vamos a convertirlo en infinito.

---

### Paso 3: Obtener el Token Infinito (Long-Lived Page Access Token)
Para obtener el token permanente que pondremos en n8n, haz una consulta HTTP en el mismo Graph Explorer o desde tu navegador web:

1. **Paso 3.A: Intercambia el Token por uno de Larga Duración (60 días):**
   Haz una petición `GET` a la siguiente URL reemplazando tus datos:
   ```http
   GET https://graph.facebook.com/v20.0/oauth/access_token?
       grant_type=fb_exchange_token&
       client_id=TU_APP_ID&
       client_secret=TU_APP_SECRET&
       fb_exchange_token=TU_TOKEN_TEMPORAL_DEL_PASO_2
   ```
   *Nota: Encuentras tu `App ID` y `App Secret` en el panel de configuración básica de tu App en Meta Developers.*
   
   Esta consulta te devolverá un JSON con un nuevo token de acceso (User Access Token largo).

2. **Paso 3.B: Generar el Token de Página Infinito:**
   Con ese token de usuario largo que acabas de recibir, haz la siguiente petición `GET`:
   ```http
   GET https://graph.facebook.com/v20.0/me/accounts?access_token=TOKEN_LARGO_DEL_PASO_3_A
   ```
   Esta consulta te devolverá una lista de tus páginas de Facebook. Busca la sección que corresponde a tu página de Contexia. Allí verás dos campos clave:
   * `"id"`: El ID de tu página de Facebook.
   * `"access_token"`: **¡Este es tu Token de Acceso de Página Infinito!** Cópialo y guárdalo de forma muy segura.

---

### Paso 4: Configurar la Publicación Automática en n8n
Ahora que tienes el token permanente, cambiar tu workflow local para que publique solo toma 2 pasos:

1. **Abre tu Workflow en n8n:**
   * Entra al workflow `WF-04-creacion-borradores` (o el flujo donde publicas).
   * Localiza el nodo de publicación final. Actualmente, es un nodo que guarda el post en la base de datos o te manda el borrador por correo.
2. **Agregar el nodo de HTTP Request de Meta:**
   * Crea un nuevo nodo de tipo **HTTP Request** justo después de que el post sea aprobado.
   * Configúralo así:
     * **Method:** `POST`
     * **URL:** `https://graph.facebook.com/v20.0/TU_PAGE_ID/feed` (reemplaza por el ID de tu página).
     * **Authentication:** Selecciona `Query Parameters` o `Header`.
     * **Headers / Parameters:**
       * Llave: `access_token`
       * Valor: *(Pega aquí tu Token de Página Infinito)*
     * **Body Content Type:** `JSON`
     * **JSON Parameters:**
       * Llave: `message`
       * Valor: `={{ $json.copy_body }}` (el copy humanizado generado por Taty).
3. **Activar el flujo:** ¡Haz clic en ejecutar y el post se publicará automáticamente en tu página de Facebook en vivo en menos de un segundo!

---

## Resolución de Problemas (Troubleshooting)

* **Error: "This token has expired"**
  * *Causa:* Usaste el Token Temporal del Paso 2 en lugar del Token Infinito del Paso 3.B. Repite el Paso 3 para obtener el token perpetuo.
* **Error: "Requires pages_manage_posts permission"**
  * *Causa:* No aceptaste todos los permisos en el popup de autorización de Facebook. Vuelve a iniciar el Paso 2 en el Graph Explorer y asegúrate de marcar tu página de Contexia con todos los checks activos.
