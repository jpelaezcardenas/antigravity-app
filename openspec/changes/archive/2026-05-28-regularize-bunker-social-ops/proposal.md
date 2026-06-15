# Regularize Bunker Social Ops

## Summary
Formalize the Social Ops work that already exists in `antigravity-app` so the Bunker becomes the canonical operational surface again.

This change keeps the current Bunker live aesthetic, preserves **Social Media OPs Systems** as the organic content engine, and makes the backend/UI contract explicit in OpenSpec before further implementation.

## Why
- The current Social Ops stack is already split across backend FastAPI and the Bunker admin UI, but the intent is not yet captured in OpenSpec.
- `Ideas` and `Metrics` are already wired to FastAPI and should remain the authoritative path, not n8n or the retired `contexia-content-os` repo.
- The approval queue is the human-in-the-loop gate for sensitive actions and outbound drafts, so it needs to remain explicit in the spec.
- `Onboarding 21D` should live in the sidebar onboarding entry only, not duplicated inside `Operaciones`.

## Scope
- Keep the current Bunker shell, sidebar behavior, search bar, and dark/cyan visual language.
- Update the Bunker subtitle to:
  - `Motor de contenido orgánico para Facebook, Instagram, TikTok, LinkedIn y Telegram — Contexia.`
- Keep `Operaciones` centered on:
  - `Ideas`
  - `Calendario`
  - `Borradores`
  - `Métricas`
  - `Inbox`
  - `Pipeline`
  - `Comandos`
  - `Aprobaciones`
  - `Integraciones`
- Keep `Ideas` and `Métricas` on FastAPI-backed endpoints.
- Keep `Approval Queue` as the human-in-the-loop control point.
- Remove operational dependence on the dead `contexia-content-os` deployment and avoid reintroducing n8n into critical Social Ops paths.

## Non-goals
- No visual redesign of the Bunker shell.
- No refactor of the Social Ops domain model beyond what is needed to formalize the existing behavior.
- No re-architecture into a new content platform.
- No new manual specs outside OpenSpec.

## Success Signals
- The Bunker admin experience still looks and feels like the current live shell.
- The sidebar exposes `Onboarding` as its own entry, with no duplicate onboarding block inside `Operaciones`.
- `Ideas` and `Métricas` continue to work through FastAPI only.
- The approval workflow remains human-reviewed before sensitive actions are executed.
- The OpenSpec change is ready for `/opsx:apply`.
