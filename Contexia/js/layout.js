/**
 * Contexia - Layout con Sidebar basado en Roles
 */

document.addEventListener('DOMContentLoaded', () => {
    // 0. Inject Global Theme CSS
    const themeLink = document.createElement('link');
    themeLink.rel = 'stylesheet';
    themeLink.href = './assets/css/theme.css';
    document.head.appendChild(themeLink);

    // Get current user and role
    const user = window.auth ? window.auth.getUser() : null;
    const role = user ? user.role : 'guest';

    // Define menu items with role access
    const menuItems = {
        dashboards: {
            title: 'Dashboards',
            items: [
                { href: 'pulso_diario.html', icon: 'dashboard', label: 'Flujo de Caja', module: 'pulso_diario', roles: ['empresa', 'contador', 'admin'] },
                { href: 'panel_empresario.html', icon: 'store', label: 'Mi Empresa', module: 'panel_empresario', roles: ['empresa', 'admin'] },
                { href: 'panel_firma.html', icon: 'business_center', label: 'Panel Firma', module: 'panel_firma', roles: ['contador', 'admin'] }
            ]
        },
        operativo: {
            title: 'Operativo',
            items: [
                { href: 'conciliacion.html', icon: 'account_balance', label: 'Conciliación', module: 'conciliacion', roles: ['empresa', 'contador', 'admin'] },
                { href: 'tesoreria.html', icon: 'payments', label: 'Tesorería', module: 'tesoreria', roles: ['empresa', 'contador', 'admin'] },
                { href: 'documentos.html', icon: 'description', label: 'Documentos', module: 'documentos', roles: ['empresa', 'contador', 'admin'] }
            ]
        },
        inteligencia: {
            title: 'Inteligencia',
            items: [
                { href: 'centinela.html', icon: 'shield', label: 'Centinela Fiscal', module: 'centinela', roles: ['empresa', 'contador', 'admin'] },
                { href: 'oraculo.html', icon: 'psychology', label: 'Análisis de Riesgo', module: 'oraculo', roles: ['empresa', 'contador', 'admin'] },
                { href: 'benchmarking.html', icon: 'query_stats', label: 'Benchmarking', module: 'benchmarking', roles: ['empresa', 'contador', 'admin'] },
                { href: 'copiloto.html', icon: 'smart_toy', label: 'Copiloto IA', module: 'copiloto', roles: ['empresa', 'contador', 'admin'] }
            ]
        }
    };

    // Filter menu items based on role
    function getVisibleItems(items) {
        return items.filter(item => {
            const hasFullAccess = item.roles.includes(role);
            const hasViewAccess = item.viewOnly && item.viewOnly.includes(role);
            return hasFullAccess || hasViewAccess;
        });
    }

    // Check if item is view-only for current role
    function isViewOnly(item) {
        return item.viewOnly && item.viewOnly.includes(role);
    }

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
        /* Sidebar styles - Using Logo Navy Colors */
        #cx-sidebar {
            width: 260px;
            flex-shrink: 0;
            background: linear-gradient(180deg, #1E3D59 0%, #0F2A42 100%);
            border-right: 1px solid #2D4A63;
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
            background-color: #F8FAFB;
            height: 100vh;
            position: relative;
            color: #1e293b;
        }
        .dark #cx-main-content {
            background-color: #f8fafc;
            color: #1e293b;
        }
        
        /* Scrollbar for sidebar */
        #cx-sidebar nav::-webkit-scrollbar {
            width: 4px;
        }
        #cx-sidebar nav::-webkit-scrollbar-thumb {
            background-color: #2D4A63;
            border-radius: 4px;
        }

        /* View only badge */
        .view-only-badge {
            font-size: 8px;
            padding: 2px 4px;
            border-radius: 4px;
            background: rgba(225, 154, 77, 0.2);
            color: #E19A4D;
            margin-left: auto;
        }
    `;
    document.head.appendChild(style);

    // 2. Wrap existing content
    const contentWrapper = document.createElement('div');
    contentWrapper.id = 'cx-main-content';

    while (document.body.firstChild) {
        contentWrapper.appendChild(document.body.firstChild);
    }
    document.body.appendChild(contentWrapper);

    // 3. Build navigation HTML based on role
    function buildNavigation() {
        let navHTML = '';

        for (const section in menuItems) {
            const sectionData = menuItems[section];
            const visibleItems = getVisibleItems(sectionData.items);

            if (visibleItems.length === 0) continue;

            navHTML += `<p class="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest ${section !== 'dashboards' ? 'mt-6' : ''} mb-2">${sectionData.title}</p>`;

            visibleItems.forEach(item => {
                navHTML += renderLink(item.href, item.icon, item.label, isViewOnly(item));
            });
        }

        return navHTML;
    }

    // Helper to render links
    function renderLink(href, icon, label, viewOnly = false) {
        const currentPath = window.location.pathname.split('/').pop();
        const isActive = currentPath === href;

        const activeClass = isActive
            ? 'bg-[#5A9A8B]/15 text-[#7AB5A7] border-[#5A9A8B]/50'
            : 'text-slate-300 hover:bg-[#2D4A63] hover:text-white border-transparent';

        const activeIcon = isActive ? 'text-[#7AB5A7]' : 'text-slate-400 group-hover:text-white';

        const viewOnlyBadge = viewOnly ? '<span class="view-only-badge">Solo ver</span>' : '';

        return `
        <a href="${href}" class="group flex items-center gap-3 px-3 py-2 rounded-lg border border-transparent transition-all ${activeClass}">
            <span class="material-symbols-outlined text-[20px] ${activeIcon}">${icon}</span>
            <span class="text-xs font-medium">${label}</span>
            ${viewOnlyBadge}
        </a>
        `;
    }

    // Get company display info (no personal name shown)
    const companyName = user ? user.company : 'Empresa';
    const companyNit = user ? (user.companyNit || '') : '';
    const companyLogo = user ? (user.companyLogo || '') : '';
    const userRole = user ? user.roleLabel : 'Rol';

    // Generate company logo HTML - use initials if no logo
    const companyInitials = companyName.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
    const logoHTML = companyLogo
        ? `<img src="${companyLogo}" alt="${companyName}" class="size-8 rounded-lg object-contain bg-slate-100 p-0.5" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
           <div class="size-8 rounded-lg bg-[#5A9A8B] items-center justify-center text-white text-xs font-bold hidden">${companyInitials}</div>`
        : `<div class="size-8 rounded-lg bg-[#5A9A8B] flex items-center justify-center text-white text-xs font-bold">${companyInitials}</div>`;

    // 4. Create Sidebar Structure (only Contexia logo + text)
    const sidebar = document.createElement('aside');
    sidebar.id = 'cx-sidebar';
    sidebar.innerHTML = `
        <div class="h-16 shrink-0 flex items-center gap-3 px-6 border-b border-[#2D4A63] bg-[#1E3D59]/80 backdrop-blur">
            <img src="./assets/img/logo.png" alt="Contexia Logo" class="h-10 w-auto object-contain">
            <span class="font-bold text-lg tracking-tight text-white">Contexia</span>
        </div>
        
        <nav class="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1">
            ${buildNavigation()}
        </nav>

        <div class="p-4 border-t border-[#2D4A63] bg-[#1E3D59]/50">
            <button onclick="window.auth.logout()" class="flex items-center gap-3 w-full px-3 py-2 text-slate-300 hover:text-white hover:bg-[#2D4A63] rounded-lg transition-colors group">
                <span class="material-symbols-outlined group-hover:text-[#E19A4D] transition-colors">logout</span>
                <span class="text-sm font-medium">Cerrar Sesión</span>
            </button>
        </div>
    `;

    // Insert Sidebar at the very beginning of body
    document.body.insertBefore(sidebar, document.body.firstChild);

    // 5. Create Top Bar with Company Info (positioned at top right of main content)
    const topBar = document.createElement('div');
    topBar.id = 'cx-topbar';
    topBar.className = 'sticky top-0 z-40 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-end';
    topBar.innerHTML = `
        <div class="flex items-center gap-3 bg-slate-50 rounded-xl px-3 py-2 border border-slate-200">
            ${logoHTML}
            <span class="text-sm font-bold text-slate-900">${companyName}</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#5A9A8B]/10 text-[#5A9A8B]">
                ${userRole}
            </span>
        </div>
    `;

    // Insert Top Bar at the beginning of main content
    const mainContent = document.getElementById('cx-main-content');
    if (mainContent && mainContent.firstChild) {
        mainContent.insertBefore(topBar, mainContent.firstChild);
    }
});

