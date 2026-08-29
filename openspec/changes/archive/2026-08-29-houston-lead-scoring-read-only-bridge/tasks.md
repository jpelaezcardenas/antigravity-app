# Tasks: houston-lead-scoring-read-only-bridge

## 1. Persist reference docs

- [x] 1.1 Add `docs/integrations/houston-plan-integracion.md` (integration plan, founder-produced).
- [x] 1.2 Add `docs/integrations/houston-playbook-ventas.md` (sales playbook content uploaded to
      Houston).

## 2. Update canon

- [x] 2.1 Add a short addendum to `ARCHITECTURE.md` Decision #20 (HubSpot section) noting Houston
      consumes the existing bridge read-only via Composio, never writes back.

## 3. Close the master plan's Subdomain 7 question

- [x] 3.1 Document in design.md (done) that no `run_creative_loop`/`manus_draft_hooks`
      generalization is needed — Houston is read-only lead-scoring, not outreach generation.

## Stage 11. Deploy to Production

Not applicable — docs-only change, no backend/frontend code touched, no deploy required.

- [x] 11.1 git commit + push to main (docs-only, no build/deploy triggered by content)
