// import { db } from './db.js';

window.seeder = {
    run() {
        console.log("[Seeder] Checking data...");
        // Check if data exists, if not, seed it
        if (db.select('movements').length === 0) {
            console.log("[Seeder] Seeding initial data...");
            this.seedMovements();
            this.seedAlerts();
            this.seedDocuments();
            console.log("[Seeder] Done.");
        }
    },

    seedMovements() {
        // Generating realistic financial movements for "Restaurante La Plaza"
        const movements = [
            { id: 1, date: this.daysAgo(0), description: "VENTAS POS - TURNO 1", amount: 2100000, type: "income", category: "sales", status: "conciliated" },
            { id: 2, date: this.daysAgo(0), description: "VENTAS POS - TURNO 2", amount: 1850000, type: "income", category: "sales", status: "conciliated" },
            { id: 3, date: this.daysAgo(0), description: "PROVEEDOR MAKRO - INSUMOS", amount: -1250000, type: "expense", category: "supplies", status: "conciliated" },
            { id: 4, date: this.daysAgo(0), description: "TRANSFERENCIA NÓMINA - C. PEREZ", amount: -1500000, type: "expense", category: "payroll", status: "conciliated" },
            { id: 5, date: this.daysAgo(1), description: "VENTAS POS - TOTAL", amount: 4200000, type: "income", category: "sales", status: "conciliated" },
            { id: 6, date: this.daysAgo(1), description: "PAGO ARRENDAMIENTO", amount: -3500000, type: "expense", category: "rent", status: "conciliated" },
            { id: 7, date: this.daysAgo(2), description: "VENTAS POS - TOTAL", amount: 3800000, type: "income", category: "sales", status: "conciliated" },
            { id: 8, date: this.daysAgo(2), description: "SERV. PUBLICOS - EPM", amount: -450000, type: "expense", category: "utilities", status: "conciliated" },
            // Pending / Exceptions
            { id: 9, date: this.daysAgo(0), description: "TRF. DESCONOCIDA 9921", amount: -200000, type: "expense", category: "uncategorized", status: "exception", reason: "no_support" },
            { id: 10, date: this.daysAgo(1), description: "PAGO PROV. AVICOLA", amount: -850200, type: "expense", category: "supplies", status: "exception", reason: "amount_mismatch", match_candidate: { amount: 850000, id: 99 } }
        ];
        db.initTable('movements', movements);
    },

    seedAlerts() {
        const alerts = [
            { id: 1, type: "fiscal", severity: "high", title: "Riesgo Fiscal ALTO", description: "Proveedor 'Servicios X' reportado en boletín de deudores morosos.", date: this.daysAgo(0), status: "active" },
            { id: 2, type: "liquidity", severity: "medium", title: "Liquidez Estrecha", description: "Proyección de caja negativa para el próximo viernes.", date: this.daysAgo(0), status: "active" },
            { id: 3, type: "compliance", severity: "low", title: "Documento Pendiente", description: "Falta RUT del proveedor nuevo ingresado ayer.", date: this.daysAgo(1), status: "active" }
        ];
        db.initTable('alerts', alerts);
    },

    seedDocuments() {
        const documents = [
            { id: 1, provider: "Tigo Une", type: "XML", amount: 340500, status: "parsed", date: this.daysAgo(0), time: "10:42 AM" },
            { id: 2, provider: "DistriHogar", type: "XML", amount: 1250500, status: "parsed", date: this.daysAgo(0), time: "10:15 AM" },
            { id: 3, provider: "Office Supplies", type: "PDF", amount: 0, status: "error", date: this.daysAgo(0), time: "09:55 AM" }
        ];
        db.initTable('documents', documents);
    },

    daysAgo(n) {
        const d = new Date();
        d.setDate(d.getDate() - n);
        // Return only YYYY-MM-DD for simpler checking
        return d.toISOString().split('T')[0];
    }
};
