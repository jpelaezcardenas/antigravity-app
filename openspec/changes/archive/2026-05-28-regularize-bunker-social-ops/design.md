# Design

## Overview
This change formalizes the current Social Ops architecture rather than replacing it.

The implementation should keep the Bunker UI shell intact, treat `Social Media OPs Systems` as the operating surface for organic content, and keep FastAPI as the backend source of truth for the operational paths.

## Key Decisions

### 1. Preserve the Bunker shell
- Keep the current sidebar-first, dark/cyan admin aesthetic.
- Keep the top search bar and current shell layout.
- Only adjust labels and placement where the spec requires it.

### 2. Make Onboarding a dedicated sidebar destination
- `Onboarding 21D` belongs in the sidebar onboarding entry.
- The onboarding workflow must not be duplicated inside `Operaciones`.
- The sidebar remains the primary navigation surface for onboarding-driven work.

### 3. Keep Social Ops backend consolidated in FastAPI
- `apps/backend/presentation/social_ops_endpoints.py` remains the single backend router for Social Ops.
- `apps/backend/presentation/router.py` already mounts the router under `/social-ops`; that should stay the canonical API surface.
- The dead `contexia-content-os` deployment should be treated as retired operationally, not as a runtime dependency.

### 4. Keep Ideas and Metrics on FastAPI only
- `frontend/dashboard/src/components/ops/IdeasOps.tsx` and `frontend/dashboard/src/components/ops/MetricasDashboard.tsx` already call the FastAPI Social Ops endpoints.
- This change should preserve that path and prevent regressions back to n8n or the retired Content OS repo.

### 5. Preserve human-in-the-loop approvals
- Any outbound draft or sensitive action must remain `pending_approval` until approved by a human.
- The approval queue must continue to support approve/reject actions as the operational gate.

## Validation Strategy
- Verify the Bunker shell renders with the updated subtitle and navigation placement.
- Verify Social Ops endpoints remain reachable through the FastAPI backend.
- Verify `Ideas` and `Métricas` continue to consume FastAPI responses.
- Verify onboarding is only exposed from the sidebar entry and not duplicated in `Operaciones`.
- Verify the approval queue remains the final human decision point.

## Risks
- The repo already contains several unrelated working-tree changes; this change must remain narrowly scoped.
- Assets and local runtime configuration may differ between local and production Bunker builds.
- If any hidden dependency still points at the dead `contexia-content-os` deployment, the operational cleanup is incomplete.
