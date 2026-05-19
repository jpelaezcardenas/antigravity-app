// import { db } from './db.js'; // Removed for global usage

window.api = {
    // --- Pulse / Dashboard ---
    async getPulse() {
        // Simulate network latency
        await new Promise(r => setTimeout(r, 400));

        const movements = db.select('movements');
        const todayStr = new Date().toISOString().split('T')[0];

        // Sales Yesterday
        // In real app we would filter by exact date. For mock, we take logic of 'daysAgo(1)' from seeder
        const salesYesterday = movements
            .filter(m => m.type === 'income' && m.category === 'sales')
            .reduce((sum, m) => sum + m.amount, 0); // Simplified summation

        // Available Cash (Mocked calculation)
        const income = movements.filter(m => m.type === 'income').reduce((sum, m) => sum + m.amount, 0);
        const expense = movements.filter(m => m.type === 'expense').reduce((sum, m) => sum + m.amount, 0);
        const cashToday = 15000000 + (income + expense); // Starting balance 15M + net flow

        return {
            salesYesterday,
            expensesYesterday: 1800000, // Mocked for simplicity
            cashToday,
            netMovement: salesYesterday - 1800000,
            trend: 'up'
        };
    },

    async getRecentMovements() {
        await new Promise(r => setTimeout(r, 300));
        return db.select('movements').slice(0, 5); // Get first 5
    },

    async getAlerts() {
        await new Promise(r => setTimeout(r, 300));
        return db.select('alerts').filter(a => a.status === 'active');
    },

    // --- Reconciliation ---
    async getExceptions() {
        await new Promise(r => setTimeout(r, 300));
        return db.select('movements').filter(m => m.status === 'exception');
    },

    async resolveException(id, action) {
        console.log(`[API] Resolving exception ${id} with action: ${action}`);
        db.update('movements', id, { status: 'conciliated', resolution: action });
        return { success: true };
    },

    // --- Centinela ---
    async blockTransaction(id) {
        // Logic to block logic
        return { success: true, status: 'blocked' };
    }
};
