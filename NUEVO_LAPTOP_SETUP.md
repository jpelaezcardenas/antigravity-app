# 🚀 Setup Contexia en Nuevo Laptop

**Fecha de creación:** 2026-05-13  
**Proyecto:** Contexia Shadow Audit  
**Estado:** Listo para migración

---

## ✅ ANTES DE MIGRAR

Todo está commiteado y listo en:
- **Repositorio:** `https://github.com/jpelaezcardenas/Contexia`
- **Rama principal:** `main`
- **Commits pendientes:** 0 (TODO limpio)

---

## 📋 REQUISITOS PARA EL NUEVO LAPTOP

### Software
- [ ] **Node.js** v18+ (https://nodejs.org/)
- [ ] **Git** (https://git-scm.com/)
- [ ] **Antigravity** (https://antigravity.dev/)
- [ ] **Claude** (Web o extensión)
- [ ] **Codex** (si quieres VSCode)
- [ ] **npm** (incluido con Node.js)

### Hardware Recomendado
- **RAM:** Mínimo 16GB (idealmente 32GB para desarrollo cómodo)
- **Almacenamiento:** 50GB libre (para node_modules + compilaciones)
- **CPU:** Intel i7+ o equivalente

---

## 🔧 SETUP EN NUEVO LAPTOP

### Paso 1: Clonar el repositorio
```bash
cd C:\Users\tu-usuario\Projects\
git clone https://github.com/jpelaezcardenas/Contexia.git
cd Contexia
```

### Paso 2: Instalar dependencias
```bash
cd contexia-wizard
npm install
```

### Paso 3: Configurar variables de entorno
Crear archivo `.env.local` en `contexia-wizard/`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-supabase-url.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
RESEND_API_KEY=your-resend-api-key
```

### Paso 4: Abrir en Antigravity
1. Abre Antigravity
2. Apunta a: `C:\Users\tu-usuario\Projects\Contexia\`
3. Espera a que indexe (~30 segundos)

### Paso 5: Desarrollo local
```bash
# En contexia-wizard/
npm run dev
```
Abre: `http://localhost:3000`

### Paso 6: Cambios finales
- Actualizar `.env.local` con tus credenciales Supabase/Resend
- Configurar webhook Cal.com en: `https://contexia.online/wizard/api/cal/webhook`

---

## 📁 ESTRUCTURA CLAVE

```
Contexia/
├── contexia-wizard/          ← Next.js app principal
│   ├── app/                  ← App router + API routes
│   ├── components/           ← React components
│   ├── pdf/                  ← DiagnosticoPDF (dark theme ✅)
│   ├── lib/                  ← Utilidades y config
│   └── package.json
├── Contexia_Dashboard/       ← React dashboard
├── docs/                     ← Documentación
└── README.md
```

---

## 🔄 WORKFLOW RECOMENDADO

### Con Antigravity
```
1. Abre Antigravity → Contexia/
2. Usa "Code with Agent" para ediciones complejas
3. Haz cambios
4. Commit: git commit -m "..."
5. Push: git push origin main
```

### Con Codex (VSCode)
```
1. Abre VSCode en Contexia/
2. Usa Codex para completar código
3. Haz cambios
4. Commit y push
```

### Con Claude Web
```
1. Usa aquí para análisis y planning
2. Pasar archivos como contexto
3. Recibir cambios de código
4. Implementar en local
```

---

## 🧪 VERIFICAR QUE TODO FUNCIONA

```bash
# Test 1: Build
cd contexia-wizard && npm run build

# Test 2: Dev server
npm run dev

# Test 3: Verificar archivos críticos
ls contexia-wizard/pdf/DiagnosticoPDF.tsx
ls contexia-wizard/app/api/cal/webhook/route.ts
```

---

## 🎯 FEATURES IMPLEMENTADAS

| Feature | Estado | Archivo |
|---------|--------|---------|
| Shadow Audit Wizard | ✅ Completo | contexia-wizard/components/wizard/ |
| PDF Dark Theme | ✅ Diseñado | contexia-wizard/pdf/DiagnosticoPDF.tsx |
| Internal Alerts | ✅ Wired | contexia-wizard/lib/notifications.ts |
| Cal.com Webhook | ⏳ Pendiente config | contexia-wizard/app/api/cal/webhook/ |
| Prefill Flow | ✅ Working | contexia-wizard/app/wizard-client.tsx |

---

## 📞 CONTACTOS CONFIGURADOS

**Email interno para alertas:**
- jpelaezcardenas@gmail.com
- tatybarbosav91@gmail.com

**Cal.com Booking:**
- https://cal.com/juan-david-pelaez-cardenas-jrurh5/30min

---

## 🚀 DESPUÉS DE SETUP

1. [ ] Verificar que Antigravity funciona
2. [ ] Verificar que dev server corre sin errores
3. [ ] Testear prefill flow: `localhost:3000/wizard/?prefill=lead-caliente`
4. [ ] Configurar Cal.com webhook en production
5. [ ] Hacer primer commit con cambios locales

---

**¿Preguntas?** Usa Claude Web o Codex para ayuda rápida.

**Última actualización:** 2026-05-13
