/**
 * Contexia Mock Database (LocalStorage Wrapper)
 * Acts as a simple ORM for browser persistence.
 */

const DB_PREFIX = 'cx_';

window.db = {
    // Initialize a table if not exists
    initTable(table, defaultData = []) {
        if (!localStorage.getItem(DB_PREFIX + table)) {
            localStorage.setItem(DB_PREFIX + table, JSON.stringify(defaultData));
            console.log(`[DB] Table '${table}' initialized.`);
        }
    },

    // Get all records from a table
    select(table) {
        const data = localStorage.getItem(DB_PREFIX + table);
        return data ? JSON.parse(data) : [];
    },

    // Find one recording matching a predicate
    find(table, predicate) {
        const rows = this.select(table);
        return rows.find(predicate);
    },

    // Insert a new record
    insert(table, record) {
        const rows = this.select(table);
        // Auto-increment ID simulation
        if (!record.id) {
            record.id = rows.length > 0 ? Math.max(...rows.map(r => r.id)) + 1 : 1;
        }
        rows.push(record);
        this.save(table, rows);
        return record;
    },

    // Update a record
    update(table, id, updates) {
        const rows = this.select(table);
        const index = rows.findIndex(r => r.id === id);
        if (index !== -1) {
            rows[index] = { ...rows[index], ...updates };
            this.save(table, rows);
            return rows[index];
        }
        return null;
    },

    // Save full table
    save(table, data) {
        localStorage.setItem(DB_PREFIX + table, JSON.stringify(data));
    },

    // Wipe everything (for debugging)
    nuke() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(DB_PREFIX)) localStorage.removeItem(key);
        });
        console.log("[DB] Nuked.");
    }
};
