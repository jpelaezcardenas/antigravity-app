document.addEventListener('DOMContentLoaded', () => {
    // 1. Inject CSS
    const style = document.createElement('style');
    style.textContent = `
        /* Layout overrides */
        body {
            display: flex !important;
            flex-direction: row !important;
            min-height: 100vh !important;
            overflow: hidden !important;
        }
        /* Sidebar styles */
        #cx-sidebar {
            width: 260px;
            flex-shrink: 0;
            background-color: #0f172a; /* slate-900 */
            border-right: 1px solid #1e293b; /* slate-800 */
            display: flex;
            flex-direction: column;
            color: white;
            transition: all 0.3s ease;
            z-index: 50;
        }
        /* Main content wrapper */
        #cx-main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            overflow-x: hidden;
            background-color: #ffffff; /* Pure white */
            height: 100vh;
            position: relative;
            color: #1e293b; /* slate-800 text default */
        }
        /* Remove or override dark mode background for main content if needed for mixed mode */
        .dark #cx-main-content {
            background-color: #f8fafc; /* Keep light/white even in 'dark' mode if user requested mixed layout */
            color: #1e293b;
        }
        
        /* Scrollbar for sidebar */
        #cx-sidebar nav::-webkit-scrollbar {
            width: 4px;
        }
        #cx-sidebar nav::-webkit-scrollbar-thumb {
            background-color: #334155;
            border-radius: 4px;
        }
    `;
    document.head.appendChild(style);

    // 2. Wrap existing content
    // We assume everything currently in body is "page content"
    const contentWrapper = document.createElement('div');
    contentWrapper.id = 'cx-main-content';

    // Move all children of body into wrapper (except scripts if possible, but moving them is usually fine)
    while (document.body.firstChild) {
        contentWrapper.appendChild(document.body.firstChild);
    }
    document.body.appendChild(contentWrapper);

    // 3. Create Sidebar Structure
    const sidebar = document.createElement('aside');
    sidebar.id = 'cx-sidebar';
    sidebar.innerHTML = `
        <div class="h-16 shrink-0 flex items-center gap-3 px-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur">
            <div class="size-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-500/20">CX</div>
            <span class="font-bold text-lg tracking-tight text-white">Contexia</span>
        </div>
        
        <nav class="flex-1 overflow-y-auto py-6 px-3 flex flex-col gap-1">
            <p class="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Dashboards</p>
            ${renderLink('pulso_diario.html', 'dashboard', 'Pulso Diario')}
            ${renderLink('panel_empresario.html', 'store', 'Panel Empresario')}
            ${renderLink('panel_firma.html', 'business_center', 'Panel Firma')}
            
            <p class="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-6 mb-2">Operativo</p>
            ${renderLink('conciliacion.html', 'account_balance', 'Conciliación')}
            ${renderLink('tesoreria.html', 'payments', 'Tesorería')}
            ${renderLink('documentos.html', 'description', 'Documentos')}
            
            <p class="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-6 mb-2">Inteligencia</p>
            ${renderLink('centinela.html', 'shield', 'Centinela Fiscal')}
            ${renderLink('oraculo.html', 'psychology', 'Análisis de Riesgo')}
            ${renderLink('benchmarking.html', 'query_stats', 'Benchmarking')}
            ${renderLink('copiloto.html', 'smart_toy', 'Copiloto Fiscal IA')}
        </nav>

        <div class="p-4 border-t border-slate-800 bg-slate-900/50">
            <button onclick="window.auth.logout()" class="flex items-center gap-3 w-full px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors group">
                <span class="material-symbols-outlined group-hover:text-red-400 transition-colors">logout</span>
                <span class="text-sm font-medium">Cerrar Sesión</span>
            </button>
        </div>
    `;

    // Helper to render links
    function renderLink(href, icon, label) {
        // Simple check if current path contains the href (e.g. /pulso_diario.html)
        const currentPath = window.location.pathname.split('/').pop();
        const isActive = currentPath === href;

        const activeClass = isActive
            ? 'bg-indigo-600/10 text-indigo-400 border-indigo-600/50'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white border-transparent';

        const activeIcon = isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-white';

        return `
        <a href="${href}" class="group flex items-center gap-3 px-3 py-2 rounded-lg border border-transparent transition-all ${activeClass}">
            <span class="material-symbols-outlined text-[20px] ${activeIcon}">${icon}</span>
            <span class="text-xs font-medium">${label}</span>
        </a>
        `;
    }

    // Insert Sidebar at the very beginning of body
    document.body.insertBefore(sidebar, document.body.firstChild);
});
