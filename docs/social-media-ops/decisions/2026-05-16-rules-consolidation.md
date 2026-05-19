# Decision: Consolidación de Archivos de Reglas

- **Fecha:** 2026-05-16
- **Estado:** Implementado
- **Decidido por:** Antigravity (aprobado por operador)

## Contexto
El repo tenía 3 archivos de reglas con contenido duplicado y riesgo de drift:
1. `rules.md` (root) — 102 líneas, versión más completa
2. `.antigravity/rules.md` — 26 líneas, subset
3. `.agents/rules/rules.md` — vacío (solo YAML frontmatter)

## Decisión
- `.agents/rules/rules.md` → **archivo canónico** (single source of truth)
- `.antigravity/rules.md` → **puntero** al archivo canónico
- `rules.md` (root) → se mantiene como copia de lectura humana

## Alternativas consideradas
| Opción | Descartada por |
|:-------|:---------------|
| Mantener 3 archivos independientes | Drift inevitable, ya pasó |
| Eliminar .antigravity/rules.md | Puede romper compatibilidad con Antigravity |
| Mover todo a root rules.md | .agents/rules/ es el estándar del tooling |

## Consecuencias
- Ediciones futuras de reglas van a `.agents/rules/rules.md`
- `.antigravity/rules.md` se actualiza automáticamente (es solo un puntero)
- root `rules.md` se puede actualizar periódicamente como espejo
