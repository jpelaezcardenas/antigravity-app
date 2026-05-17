# PWA Setup para Contexia

La app está configurada como PWA instalable. Aquí está qué se necesita para que funcione completamente.

## ✅ Qué está listo

- ✅ Manifest dinámico en `app/manifest.ts`
- ✅ Service Worker en `public/sw.js`
- ✅ Metadata PWA en `app/layout.tsx`
- ✅ Registro de SW en `app/register-sw.tsx`
- ✅ Estrategia de cache (network-first HTML, cache-first assets)

## 📋 Qué falta: Iconos

La PWA **funciona sin iconos**, pero no se verá completa. Necesitas reemplazar:

```
public/icons/
├── icon-192x192.png           (192x192px, sin fondo)
├── icon-192x192-maskable.png  (192x192px, ícono cuadrado para adaptive icons)
├── icon-512x512.png           (512x512px, sin fondo)
└── icon-512x512-maskable.png  (512x512px, ícono cuadrado)
```

### Cómo generar los iconos

**Opción 1: Usar Figma o diseñador**
1. Exporta el logo de Contexia en 512x512 como PNG con fondo transparente
2. En tu herramienta de diseño, crea versiones "maskable" (cuadradas, se verá dentro de un círculo adaptativo)
3. Exporta los 4 archivos a `public/icons/`

**Opción 2: Usar herramienta online**
1. Ve a [favicon.io](https://favicon.io) o [realfavicongenerator.net](https://realfavicongenerator.net)
2. Sube tu logo (preferiblemente SVG o PNG de alta res)
3. Descarga los archivos PNG de 192x192 y 512x512
4. Copia a `public/icons/`
5. Para maskable, crea versiones cuadradas con margin (20% padding interno)

**Opción 3: Script de generación (requiere ImageMagick)**

```bash
# Si tienes ImageMagick instalado:
node scripts/generate-icons.js
```

Este script busca tu logo en `assets/logo.svg` o `assets/logo.png` y genera las variantes.

## 🧪 Testing

### En desarrollo

```bash
npm run dev
```

Luego en Chrome DevTools (F12):
- Ve a **Application** > **Manifest**
- Verifica que el manifest se carga (verde)
- Ve a **Service Workers**
- Verifica que el SW está registrado y activo

### Instalar en mobile

1. **Android Chrome**:
   - Abre https://www.contexia.online/app
   - Chrome mostrará "Instalar app" en el menú (⋮)
   - Toca "Instalar" → se añade a pantalla de inicio

2. **iOS Safari** (PWA limitada):
   - Safari > Compartir > Añadir a pantalla de inicio
   - Se instala pero **sin full capabilities**

3. **Desktop Chrome**:
   - Abre https://www.contexia.online/app
   - Se mostrará un botón "Instalar" en URL bar
   - Instala como app nativa en Windows/Mac

## 📊 Verificar instalabilidad

Usa [PWA Builder](https://www.pwabuilder.com):
1. Ingresa https://www.contexia.online/app
2. Analiza el reporte
3. Debe mostrar: ✅ Manifest, ✅ SW, ✅ HTTPS, ✅ Icons

## 🎯 Qué hace cada archivo

| Archivo | Función |
|---------|----------|
| `app/manifest.ts` | Define nombre, icons, start_url, theme_color para instalación |
| `public/sw.js` | Cache estrategia: network-first HTML, cache-first assets |
| `lib/sw-register.ts` | Hook para registrar SW desde cliente |
| `app/register-sw.tsx` | Componente que monta el registro del SW |
| `app/layout.tsx` | Metadata PWA: apple-web-app, theme-color, manifest link |

## 📈 Próximos pasos (fuera del scope actual)

- [ ] Notificaciones push (requiere backend/service)
- [ ] Sincronización en background (requiere Backend Sync API)
- [ ] Estrategia offline avanzada (cachear más páginas)
- [ ] App shortcuts personalizadas por usuario
- [ ] Web App Install Banner customizado
- [ ] Detección de "instalación completada" para analytics

## 🐛 Troubleshooting

**"Service Worker no se registra"**
- Verificar console en DevTools
- PWA requiere HTTPS (o localhost)
- Verificar que `/sw.js` existe y no hay 404

**"No aparece botón de instalar"**
- Necesitas los 4 iconos en `public/icons/`
- Necesitas HTTPS en producción
- Necesitas manifest accesible en `/manifest.json`

**"Iconos se ven borrosos en Android"**
- Usa los archivos de 512x512px
- Asegúrate que no están comprimidos agresivamente
- Android descala automáticamente a 192x192 para launcher

## 📝 Nota sobre seguridad

El Service Worker cachea agresivamente assets estáticos. Para actualizar:
- HTML: Network-first (siempre trata de conectar)
- JS/CSS: Cache-first (pero se actualiza en segundo plano cada load)
- Versión de cache: `v1` en `public/sw.js` — incrementa si necesitas forzar reload

Para desplegar cambios grandes:
1. Modifica `CACHE_VERSION = "v2"` en `public/sw.js`
2. El siguiente acceso limpiará caches viejos
