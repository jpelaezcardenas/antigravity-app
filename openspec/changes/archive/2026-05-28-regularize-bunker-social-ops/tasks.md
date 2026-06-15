# Tasks

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create and switch to `feature/regularize-bunker-social-ops`
- [x] 0.2 Verify the branch and capture `git status --short` baseline

## 1. Review and Update Existing Unit Tests (MANDATORY)

- [x] 1.1 Inspect current backend tests for `social_ops_endpoints` and `social_ops_service`
- [x] 1.2 Inspect frontend coverage around `BunkerApp`, `AdminShell`, `IdeasOps`, `MetricasDashboard`, and `SocialContentOps`
- [x] 1.3 Add or update tests for the subtitle, sidebar onboarding placement, and FastAPI-only ideas/metrics path

## 2. Validate Backend Social Ops Surface

- [x] 2.1 Confirm the active Social Ops router is `apps/backend/presentation/social_ops_endpoints.py`
- [x] 2.2 Confirm `/api/v1/social-ops` remains the single consolidated backend surface
- [x] 2.3 Document the endpoint inventory and confirm there is no duplicate legacy route mapping

## 3. Update Bunker Admin Shell

- [x] 3.1 Update the Bunker subtitle to `Motor de contenido organico para Facebook, Instagram, TikTok, LinkedIn y Telegram - Contexia.`
- [x] 3.2 Preserve the current live aesthetic, sidebar-first layout, and top search behavior
- [x] 3.3 Keep `Social Media OPs Systems` as the visible operations brand

## 4. Rehome Onboarding 21D

- [x] 4.1 Ensure `Onboarding 21D` is reachable from the sidebar `Onboarding` entry
- [x] 4.2 Remove the duplicated onboarding experience from `Operaciones`
- [x] 4.3 Keep `Operaciones` centered on `Ideas`, `Calendario`, `Borradores`, `Metricas`, `Inbox`, `Pipeline`, `Comandos`, `Aprobaciones`, and `Integraciones`

## 5. Preserve FastAPI Paths and HITL Approval Flow

- [x] 5.1 Keep `Ideas` and `Metricas` consuming FastAPI Social Ops endpoints only
- [x] 5.2 Keep Approval Queue as the human-in-the-loop control point for sensitive actions and outbound drafts
- [x] 5.3 Remove any residual operational dependence on `contexia-content-os` or n8n paths for critical Social Ops behavior
- [x] 5.4 Audit stale worktree copies under `.claude/worktrees` and eliminate any hardcoded Content OS endpoint references

## 6. Update Documentation and OpenSpec Artifacts

- [x] 6.1 Keep the new OpenSpec change artifacts in sync with the implementation scope
- [x] 6.2 Document the retirement of `contexia-content-os` as an operational dependency
- [x] 6.3 Document the canonical backend and frontend entry points for Social Ops

## 7. Run Unit Tests and Verify Database State (MANDATORY)

- [x] 7.1 Capture the impacted database baseline before test execution (not applicable: targeted tests ran against in-memory Social Ops state)
- [x] 7.2 Run targeted backend and frontend unit tests for the touched Social Ops paths
- [x] 7.3 Run the required broader suite or justified subset
- [x] 7.4 Verify post-test database state and restore if needed (not applicable: no persistent database state was mutated by the targeted unit suite)
- [x] 7.5 Create report `openspec/changes/regularize-bunker-social-ops/reports/YYYY-MM-DD-step-7-unit-test-and-db-verification.md`

## 8. Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 8.1 Start the backend if it is not already running
- [x] 8.2 Verify `/api/v1/social-ops/ideas` and `/api/v1/social-ops/metrics`
- [x] 8.3 Verify `generate-draft`, approval actions, and onboarding endpoints
- [x] 8.4 Verify error cases and restore any mutated state

## 9. E2E Testing with Playwright MCP (MANDATORY if applicable - AGENT MUST EXECUTE)

- [x] 9.1 Start frontend and backend services
- [x] 9.2 Open the Bunker UI and verify the shell matches the live aesthetic
- [x] 9.3 Confirm the sidebar onboarding entry and Operations tab set
- [x] 9.4 Exercise Ideas and Metrics flows through the UI
- [x] 9.5 Confirm the approval queue behaves as the human-in-the-loop gate

## 10. Final Documentation Pass (MANDATORY)

- [x] 10.1 Update any technical docs that still mention `contexia-content-os` as a live dependency
- [x] 10.2 Update API or onboarding notes if the formal contract changed
- [x] 10.3 Verify the change is ready for `/opsx:apply`
- [x] 10.4 Verify no active `contexia-content-os-production` or `/api/v1/generate` references remain in the workspace copies
