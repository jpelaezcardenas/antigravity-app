/**
 * Contexia - Sistema de Autenticación con Roles
 * Roles: empresario, contador, admin
 */

window.auth = {
    key: 'cx_session',

    // Usuarios de prueba por rol
    users: {
        empresa: {
            username: 'empresa',
            password: 'empresa',
            profile: {
                name: 'Carlos Mendoza',
                role: 'empresa',
                roleLabel: 'Empresa',
                company: 'DistriFuXion AI',
                companyNit: '900.123.456-7',
                companyLogo: './assets/img/companies/distrifuxion-ai.png',
                email: 'carlos@distribucionai.com',
                avatar: 'CM',
                homePage: 'panel_empresario.html'
            }
        },
        contador: {
            username: 'contador',
            password: 'contador',
            profile: {
                name: 'Tatiana Barbosa',
                role: 'contador',
                roleLabel: 'Contadora',
                company: 'Tatiana Barbosa',
                companyNit: 'T.P. 123456-T',
                companyLogo: './assets/img/profiles/tatiana-barbosa.jpg',
                professionalCard: 'T.P. 123456-T',
                email: 'tatiana@barbosacontadores.com',
                avatar: 'TB',
                homePage: 'panel_firma.html'
            }
        },
        admin: {
            username: 'admin',
            password: 'admin',
            profile: {
                name: 'Juan Peláez',
                role: 'admin',
                roleLabel: 'Administrador',
                company: 'Juan Peláez',
                companyNit: 'C.C. 1.234.567.890',
                companyLogo: './assets/img/profiles/juan-pelaez.jpg',
                email: 'juan.pelaez@contexia.co',
                avatar: 'JP',
                homePage: 'pulso_diario.html'
            }
        }
    },

    // Permisos de módulos por rol
    permissions: {
        empresa: {
            modules: ['pulso_diario', 'panel_empresario', 'conciliacion', 'tesoreria', 'documentos', 'centinela', 'oraculo', 'benchmarking', 'copiloto'],
            viewOnly: []
        },
        contador: {
            modules: ['pulso_diario', 'panel_firma', 'conciliacion', 'tesoreria', 'documentos', 'centinela', 'oraculo', 'benchmarking', 'copiloto'],
            viewOnly: []
        },
        admin: {
            modules: ['pulso_diario', 'panel_empresario', 'panel_firma', 'conciliacion', 'tesoreria', 'documentos', 'centinela', 'oraculo', 'benchmarking', 'copiloto'],
            viewOnly: []
        }
    },

    login(username, password) {
        // Find matching user
        for (const key in this.users) {
            const user = this.users[key];
            if (user.username === username && user.password === password) {
                localStorage.setItem(this.key, JSON.stringify(user.profile));
                return { success: true, homePage: user.profile.homePage };
            }
        }
        return { success: false, message: 'Usuario o contraseña incorrectos' };
    },

    logout() {
        localStorage.removeItem(this.key);
        window.location.href = 'login.html';
    },

    checkAuth() {
        const session = localStorage.getItem(this.key);
        const isLoginPage = window.location.pathname.endsWith('login.html');

        if (!session && !isLoginPage) {
            window.location.href = 'login.html';
        } else if (session && isLoginPage) {
            const user = JSON.parse(session);
            window.location.href = user.homePage || 'pulso_diario.html';
        }
    },

    getUser() {
        const session = localStorage.getItem(this.key);
        return session ? JSON.parse(session) : null;
    },

    getRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },

    hasAccess(module) {
        const role = this.getRole();
        if (!role) return false;

        const perms = this.permissions[role];
        if (!perms) return false;

        return perms.modules.includes(module) || perms.viewOnly.includes(module);
    },

    isViewOnly(module) {
        const role = this.getRole();
        if (!role) return true;

        const perms = this.permissions[role];
        if (!perms) return true;

        return perms.viewOnly.includes(module);
    },

    getVisibleModules() {
        const role = this.getRole();
        if (!role) return [];

        const perms = this.permissions[role];
        if (!perms) return [];

        return [...perms.modules, ...perms.viewOnly];
    }
};

// Auto-run check on load
window.auth.checkAuth();
