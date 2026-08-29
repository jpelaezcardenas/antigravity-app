-- Migration 0044: allow 'pulso_diario_insight' as a valid operator_tasks.task_type
-- Date: 2026-08-29
-- The pulso-diario-agent-insight-bridge change added operator_task_service.py's
-- submit_completed_insight(), which inserts task_type='pulso_diario_insight'. The original
-- 0024 CHECK constraint was never widened to allow it, so every insert has been rejected in
-- production since deploy (confirmed live: 0 rows of this type exist). This migration is
-- additive-only — no data migration needed since no row of this type has ever been persisted.

ALTER TABLE operator_tasks DROP CONSTRAINT chk_operator_tasks_task_type;

ALTER TABLE operator_tasks ADD CONSTRAINT chk_operator_tasks_task_type CHECK (
  task_type IN (
    'post_content',
    'run_ads_ab',
    'research',
    'metrics_pull',
    'external_integration',
    'generate_doc',
    'pulso_diario_insight'
  )
);

SELECT '✅ 0044 operator_tasks_pulso_insight_type complete' AS status;
