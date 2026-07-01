# Bitácora (append-only)

> Una entrada por sesión cerrada. El líder añade al final; nunca se reescribe lo anterior.
> Esto reemplaza el hábito de volcar reportes sueltos a la raíz del repo.

---

## 2026-06-30 — Bootstrap del harness + canon vivo

- Creados: `ARCHITECTURE.md` (producto) + `../ARCHITECTURE.md` (workspace) + `HARNESS.md`.
- Harness: `.claude/agents/{leader,implementer,reviewer}.md`, `progress/`, `feature_list.json`, `init.sh`, hooks.
- Cableado: `CLAUDE.md` (imports + mapa + carve-out English-only), `openspec/config.yaml`, `CHECKPOINTS.md`.
- Limpieza: archivados los `.md` de sesión/fase de la raíz → `docs/archive/`.
- Patrón de referencia: `jpelaezcardenas/ejemplo-harness-subagentes`.
