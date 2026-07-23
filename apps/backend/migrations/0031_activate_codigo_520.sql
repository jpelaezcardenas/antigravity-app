-- Migration 0031: Activate CÓDIGO 520
-- Date: 2026-07-20
-- CÓDIGO 520 was seeded as 'inactivo' in migration 0028 (not-yet-paying prospect). The
-- founder confirmed it is now confirmed to start paying operations, so it's activated on
-- the roster. Idempotent (plain assignment).

UPDATE b2b_clients SET status = 'activo' WHERE name = 'CÓDIGO 520';

SELECT '✅ 0031 activate_codigo_520 complete' AS status;
