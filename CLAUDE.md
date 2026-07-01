---
description: This document contains all development rules and guidelines for this project, applicable to all AI agents (Claude, Cursor, Codex, Gemini, etc.).
alwaysApply: true
---

## 0. Canonical docs map (read first)

This repo's living memory. These load every session — read them, and **correct them on sight** when reality drifts.

@ARCHITECTURE.md
@HARNESS.md

- **Identity / legal / semantics** → `.antigravity/GROUND_TRUTH.md` (overrides everything on identity).
- **Product architecture** → `ARCHITECTURE.md` (containers, data flow, Caja Real, settled decisions).
- **How agents work here (harness + subagents)** → `HARNESS.md` (leader → implementer → reviewer; precedence over OpenSpec).
- **Agent roster (9 agents)** → `AGENTES.md`.
- **What we build now (deltas)** → `openspec/changes/<active>/` (the ONLY source of "what to do now").
- **Ecosystem map (all repos)** → `../ARCHITECTURE.md`.

**Living-doc rule:** if you add/remove/change a container or an external dependency, update `ARCHITECTURE.md` in the SAME OpenSpec change (see §7). Keep this map lean — it is always loaded.

## 1. Core Principles

- **Small tasks, one at a time**: Always work in baby steps, one at a time. Never go forward more than one step.
- **Test-Driven Development**: Start with failing tests for any new functionality (TDD), according to the task details.
- **Type Safety**: All code must be fully typed.
- **Clear Naming**: Use clear, descriptive names for all variables and functions.
- **Incremental Changes**: Prefer incremental, focused changes over large, complex modifications.
- **Question Assumptions**: Always question assumptions and inferences.
- **Pattern Detection**: Detect and highlight repeated code patterns.

## 2. Language Standards
- **English Only**: All technical artifacts must always use English, including:
    - Code (variables, functions, classes, comments, error messages, log messages)
    - Documentation (README, guides, API docs)
    - Jira tickets (titles, descriptions, comments)
    - Data schemas and database names
    - Configuration files and scripts
    - Git commit messages
    - Test names and descriptions

  **Carve-out (2026-06-30):** founder-facing SUMMARIES (e.g. the top section of `ARCHITECTURE.md` / `HARNESS.md` written for Juan David) MAY be bilingual (ES/EN). Everything else — code, config, agent definitions, technical doc bodies — stays English-only. Do not "correct" an intentional bilingual founder summary back to English.

## 3. Specific standards

For detailed standards and guidelines specific to different areas of the project, refer to:

- [Backend Standards](./docs/backend-standards.md) - API development, database patterns, testing, security and backend best practices
- [Frontend Standards](./docs/frontend-standards.md) - React components, UI/UX guidelines, and frontend architecture
- [Documentation Standards](./docs/documentation-standards.md) - Technical documentation structure, formatting, and maintenance guidelines, including AI standards like this document
- [OpenSpec Tasks Mandatory Steps](./docs/openspec-tasks-mandatory-steps.md) - Required checklist and execution rules when creating or updating OpenSpec `tasks.md` files

## 4. Project Skills

- Skills live in `ai-specs/skills`.
- When a request matches a skill, load and follow the corresponding `SKILL.md` automatically before continuing.
- Also load any referenced files in the skill folder (for example, `references/*.md`) when the skill requires them.

## 5. Planning Model Requirement

Planning workflows must run with Opus high reasoning.

This requirement applies to:
- `enrich-us`
- `openspec-ff-change`
- `openspec-continue-change`

Before starting any of these workflows, verify the session is using Opus high reasoning. If it is not, **self-correct** by adding `"model": "claude-opus-4-7"` to `.claude/settings.json` (use the `update-config` skill or edit directly), then continue — do not stop and ask the user. Do the same to come back to sonnet medium for any other step.

## 6. Symlink Integrity and Multi-Agent Portability

- **Canonical Source**: Keep reusable artifacts in `ai-specs` as the canonical source. Agent-specific paths (such as `.claude` and `.cursor`) should reference them through symlinks when possible.
- **Update Safety**: Whenever a file is renamed, moved, or its suffix changes, verify and update all symlinks that target it before considering the change complete.
- **New Artifact Linking**: Whenever creating a new artifact that requires multi-agent exposure (for example new agents or skills in `ai-specs`), create the corresponding symlinks from the expected agent-specific reference paths.
- **External Customization Review**: Whenever customization is introduced outside `ai-specs`, evaluate whether it should be moved into `ai-specs` and replaced with symlinks from the original locations.
- **Completion Gate**: A change is incomplete if it leaves broken symlinks, stale targets, or duplicated canonical artifacts across agent-specific folders.

## 7. Mandatory OpenSpec Artifact Updates for Post-Apply Changes

When a new fix/change request appears after `opsx:apply` (or `/apply`) and before `opsx:archive` (or `/archive`), agents must treat it as a spec update first, not as an informal "fix this quickly". It's the core principle of openspec, documentation is the source of truth.

Required order:

1. Update the current OpenSpec change artifacts that are affected (for example: scenarios, requirements/specs, and `tasks.md`). Don't add tasks as "bugfixes" but as part of the initial design, thus in the proper section
2. If artifact regeneration is needed, run the corresponding OpenSpec step (`opsx:continue`, `opsx:ff`, or equivalent) before coding.
3. Implement code only after artifacts reflect the new request.
4. Re-run verification against the updated artifacts before archiving.

Do not apply direct code-only fixes in this window without updating OpenSpec artifacts.

## 8. OpenSpec Deployment Stage (NEW — 2026-05-30)

**Purpose:** Close the loop — OpenSpec changes must reach PRODUCTION, not just get archived.

### Standard: Stage 11 is Mandatory

Every OpenSpec change MUST include:
```
proposal → design → spec → tasks → apply → [DEPLOY] → archive
```

Stage 11 (Deploy to Production) is no longer optional.

### Reference Files

- **DEPLOYMENT_STAGE/** — Symlink to `ai-specs/openspec-deployment-standard/`
  - `DEPLOYMENT_STAGE.md` — Full 11-step workflow
  - `CHECKPOINTS.md` — Objective criteria for "done" (evolves via self-improving loop)
  - `checklist-vercel.md` — Frontend deployment steps
  - `checklist-railway.md` — Backend deployment steps
  - `INTEGRATION_GUIDE.md` — How to apply to all projects

### Project-Specific Details

**Repository:** https://github.com/jpelaezcardenas/antigravity-app

**Deploy branch:** `main` (Vercel auto-deploys)

**Frontend:**
  - Tool: Vercel
  - URL: https://contexia.online/app/bunker
  - Checklist: `DEPLOYMENT_STAGE/checklist-vercel.md`

**Backend:**
  - Tool: Railway (production-175a)
  - URL: https://antigravity-app-production-175a.up.railway.app
  - Checklist: `DEPLOYMENT_STAGE/checklist-railway.md`

**Database:**
  - Tool: Supabase
  - Migrations: `apps/backend/migrations/`
  - Validation: `npm run migrate:test`

### Stage 11 Template for tasks.md

Add this section to every new OpenSpec change's `tasks.md`:

```markdown
## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green ✅)
- [ ] 11.3 Railway deploy active (if backend change)
- [ ] 11.4 Production URL: changes visible and working
- [ ] 11.5 Create report: openspec/changes/[CHANGE-ID]/reports/YYYY-MM-DD-deployment.md
```

### Self-Improving Loop

When a reviewer rejects deployment for a reason NOT in `CHECKPOINTS.md`:
1. Document the exact reason
2. Reviewer adds rule to `CHECKPOINTS.md`
3. Next changes inherit that rule automatically

Example evolution:
```
Sesión 1: Deploy falló porque falta env var en Railway
Sesión 2: CHECKPOINTS.md ahora: "[ ] Verify all env vars in Railway"
Sesión 3+: Todos verifican env vars automáticamente
```

### What "Done" Means Now

A change is truly done when:
- ✅ Spec proposed and designed
- ✅ All tasks completed
- ✅ Code implemented and tested
- ✅ PR reviewed and merged
- ✅ **Changes deployed to production (Stage 11)**
- ✅ Deployment report created
- ✅ Change archived

**Without Stage 11:** Change is incomplete, even if all tasks say "done".

### Key URLs

| System | URL |
|--------|-----|
| GitHub | https://github.com/jpelaezcardenas/antigravity-app |
| Vercel | https://vercel.com/contexia/antigravity-app/deployments |
| Railway | https://railway.app/[project]/deployments |
| Production | https://contexia.online/app/bunker |

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Build failed" in Vercel | Check Vercel logs for syntax errors |
| Changes not visible in production | Hard refresh: Ctrl+F5 |
| Railway deploy stuck | Check Railway logs for runtime errors |
| Stage 11 not in tasks.md | Add it manually (template above) |

### References

- `DEPLOYMENT_STAGE/` — All checklists and workflows
- `.antigravity/CLAUDE.md` — Antigravity IDE config
- `.antigravity2/CLAUDE.md` — Antigravity 2.0 IDE config
- `ai-specs/codex-context.md` — Codex (ChatGPT) context

## 9. Fuente canónica — contexia-app (end-user PWA)

`contexia.online/app/overview` (and `/fiscal`, `/patrimonio`, `/radar`,
`/flujo-detalle`) is the **end-user PWA** (Pulso, Centinela, Patrimonio, Radar) —
this is the MVP. The Búnker (`app/bunker.html` + `app/dashboard-assets/`) is a
**separate, internal-future AI OS surface**, not the end-user MVP.

**Canonical source:** `contexia-app/` at the root of this repo, on `main`. It is
fully tracked (see `.gitignore` — only `node_modules/`, `.next/`, `out/` are
ignored). `app/` (repo root) is a **build artifact** generated by
`cd contexia-app && npm run build` then syncing `contexia-app/out/` → `app/`.
**Never hand-edit `app/`.**

### Incident (2026-06-29) and the rule it produced

A `.gitignore` rule (`contexia-app/` with only `!contexia-app/lib/` as an
exception) caused fresh checkouts/worktrees of `contexia-app/` to be missing
almost everything except `lib/`. A session hit this, assumed the files were
genuinely gone, and **fabricated ~15 stub files** with fake mock data, replaced
4 of 5 real screens with **"coming soon" placeholders**, and **disabled
TypeScript** (`ignoreBuildErrors: true`) to force a green build — then deployed
that degraded export to production, overwriting the real PWA and the Búnker
bundle. A stale, never-versioned service worker then poisoned navigation on top
of that. Both were reverted; the real source was restored from git history
(`cd242ef^`) and the `.gitignore` bug fixed.

**Hard rules going forward:**

1. **Missing file/import ⇒ STOP and investigate the source. Never fabricate a
   stub, mock, or placeholder screen to make a build pass.** Check git history
   (`git log --diff-filter=D -- <path>`), other branches/worktrees, and ask the
   user before inventing data or UI.
2. **Never disable type-checking to unblock a build** (`ignoreBuildErrors`,
   loosened `tsconfig`, `// @ts-ignore` sprees). A red build with a clear error
   is informative; a green build with fake types hides the real problem.
3. **Never replace a real screen with a placeholder** to "make the build work."
   If a screen can't build, fix the actual cause or stop and ask — don't ship
   a regression silently.
4. **Verify visually before deploying.** "Build succeeded" is not "it works."
   Run the app (or its preview) and look at the screens that changed before
   pushing to production — see Stage 11 above.
5. **Service workers must be versioned per deploy** (bump `CACHE_VERSION`, or
   derive it from the build hash) and prefer network-first for navigation, so a
   bad deploy can't get permanently stuck behind a stale cache.

