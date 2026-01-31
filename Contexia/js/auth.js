window.auth = {
    key: 'cx_session',

    login(username, password) {
        // Mock validation
        if (username === 'admin' && password === 'admin') {
            const user = {
                username: 'Carlos Emprendedor',
                role: 'owner',
                company: 'Restaurante La Plaza',
                avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBrRPo19wFJY7gwSo3x1P8_kQkly-A1dl-8oPMQipHw6vN6YHjF6W-bvL3vFEBaEVTSVeGNEksZcsXSRWKrjYAStnrWntu8lBOtLtVITG9WsAyKvZwlfVpQJe5pDBpFnKLCQB3MqX5dvZvz2hBZ3t2JF4NEkdkT4dmxky8zkU2IbvDCQK-pGLWVH4V8fCt5RavEnljOEaqtfDQPBMIsy8Iyl3NPHl2p2MYdCswAb-rgcFdhrwYyKam0s6SXTmYmt1tKaP8GYG_yM-0'
            };
            localStorage.setItem(this.key, JSON.stringify(user));
            return { success: true };
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
            // Store return url ensuring we don't loop
            // For file:// we can't easily use query params, so we just redirect to login
            window.location.href = 'login.html';
        } else if (session && isLoginPage) {
            window.location.href = 'pulso_diario.html';
        }
    },

    getUser() {
        const session = localStorage.getItem(this.key);
        return session ? JSON.parse(session) : null;
    }
};

// Auto-run check on load
// We wrap in a try-catch or check if we are already willing to run it immediately
// Ideally we call this manually in head, but for simplicity we can run it here
// provided this script is loaded in HEAD.
window.auth.checkAuth();
