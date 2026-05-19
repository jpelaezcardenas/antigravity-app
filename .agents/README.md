# .agents/

Insumos que consumen los **agentes automáticos** del Content OS de Contexia (Claude Code, n8n y prompts del backend FastAPI).

## Estructura

```
.agents/
├── workflows/   # JSONs de n8n importables (WF-01 a WF-10)
└── rules/       # Reglas de prompting, knowledge base y formato de salida
```

## workflows/

7 flujos parametrizados y probados:

- `WF-01-intake-ideas.json` — Captura ideas desde formulario / fuentes externas
- `WF-02-generacion-ideas.json` — Generación masiva de ideas con LLM
- `WF-04-creacion-borradores.json` — Pasa idea → guión/borrador
- `WF-07-logging-publicaciones.json` — Registra cada publicación en Supabase
- `WF-08-captura-metricas.json` — Captura métricas desde Facebook/Meta
- `WF-09-scoring-posts.json` — Calcula score de cada post
- `WF-10-analisis-semanal.json` — Resumen analítico semanal

Todos llaman al backend interno en `http://localhost:8080/api/v1/llm/analyze` (en MVP local). Para producción, ajustar la URL base via variable de entorno del propio n8n.

## rules/

- `rules.md` — Reglas globales del sistema (qué SÍ y qué NO hacer al generar contenido).
- `OUTPUT_FORMAT.md` — Schema JSON esperado de los prompts (parseable y validable).
- `Base de conocimientos-Contexia.md` — ICP, dolores, voz de marca, glosario.
- `PROJECT_BRIEF.md` — Brief estratégico del proyecto.
- `DISCOVERY_TEMPLATE.md` — Discovery respondido (decisiones de arquitectura).

## Para Claude Code

Claude Code corriendo en la raíz puede:

1. Leer estas reglas como contexto cuando trabaje features de social-media-ops.
2. Sugerir cambios consistentes con la voz de marca documentada.
3. Generar/refactorizar prompts usando `OUTPUT_FORMAT.md` como contrato.
