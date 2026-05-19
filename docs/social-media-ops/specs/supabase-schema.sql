-- ============================================================
-- Contexia Content OS — Schema SQL para Supabase
-- Ejecutar en: Supabase > SQL Editor > New Query > Run
-- ============================================================

-- Habilitar extensión para UUIDs (por defecto en Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLA 1: ideas
-- Banco de ideas y backlog editorial
-- ============================================================
CREATE TABLE IF NOT EXISTS ideas (
  id                BIGSERIAL PRIMARY KEY,
  fecha_ingreso     DATE NOT NULL DEFAULT CURRENT_DATE,
  fuente            TEXT CHECK (fuente IN ('ICP_DOLOR','NOTICIA','TRENDING','RECICLAJE','MANUAL')) DEFAULT 'MANUAL',
  tema_raw          TEXT NOT NULL,
  pilar             TEXT CHECK (pilar IN ('CLARIDAD','PROTECCION','ACCION','COMUNIDAD')),
  angulo            TEXT,
  formato_sugerido  TEXT CHECK (formato_sugerido IN ('TEXTO_IMAGEN','CARRUSEL','VIDEO_CORTO','STORYTELLING')),
  dolor_icp         TEXT CHECK (dolor_icp IN ('MIEDO_DIAN','SORPRESA_TRIBUTARIA','DESORDEN','JERGA_OPACA','CEGUERA_CAJA','FORMALIZACION')),
  score_potencial   INTEGER CHECK (score_potencial BETWEEN 1 AND 10),
  status            TEXT CHECK (status IN ('NUEVA','SELECCIONADA','DESCARTADA','USADA')) DEFAULT 'NUEVA',
  notas             TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 2: calendario
-- Calendario editorial semanal
-- ============================================================
CREATE TABLE IF NOT EXISTS calendario (
  id                    BIGSERIAL PRIMARY KEY,
  semana                INTEGER NOT NULL,
  fecha_publicacion     DATE NOT NULL,
  dia_semana            TEXT GENERATED ALWAYS AS (TO_CHAR(fecha_publicacion, 'Day')) STORED,
  idea_id               BIGINT REFERENCES ideas(id) ON DELETE SET NULL,
  pilar                 TEXT CHECK (pilar IN ('CLARIDAD','PROTECCION','ACCION','COMUNIDAD')),
  formato               TEXT CHECK (formato IN ('TEXTO_IMAGEN','CARRUSEL','VIDEO_CORTO','STORYTELLING')),
  titulo_trabajo        TEXT,
  status                TEXT CHECK (status IN ('PLANIFICADO','EN_PRODUCCION','DRAFT','REVIEW','APPROVED','PUBLISHED')) DEFAULT 'PLANIFICADO',
  responsable           TEXT DEFAULT 'Operador',
  notas_editoriales     TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 3: contenido
-- Pipeline de producción de piezas
-- ============================================================
CREATE TABLE IF NOT EXISTS contenido (
  id                  BIGSERIAL PRIMARY KEY,
  cal_id              BIGINT REFERENCES calendario(id) ON DELETE CASCADE,
  hook                TEXT,
  hook_alt_1          TEXT,
  hook_alt_2          TEXT,
  hook_seleccionado   TEXT CHECK (hook_seleccionado IN ('PRINCIPAL','ALT_1','ALT_2')) DEFAULT 'PRINCIPAL',
  copy_body           TEXT,
  cta                 TEXT,
  hashtags            TEXT,
  guion_video         TEXT,
  notas_visual        TEXT,
  asset_url           TEXT,
  version             INTEGER DEFAULT 1,
  status              TEXT CHECK (status IN ('BORRADOR_IA','EDITADO_HUMANO','APROBADO','LISTO_PUBLICAR')) DEFAULT 'BORRADOR_IA',
  fecha_aprobacion    DATE,
  aprobado_por        TEXT,
  qa_humanizacion     BOOLEAN DEFAULT FALSE,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 4: publicaciones
-- Registro de posts publicados en Facebook
-- ============================================================
CREATE TABLE IF NOT EXISTS publicaciones (
  id                        BIGSERIAL PRIMARY KEY,
  content_id                BIGINT REFERENCES contenido(id) ON DELETE CASCADE,
  fecha_publicacion_real    TIMESTAMPTZ,
  plataforma                TEXT DEFAULT 'FACEBOOK',
  url_post                  TEXT,
  tipo_publicacion          TEXT CHECK (tipo_publicacion IN ('TEXTO_IMAGEN','CARRUSEL','VIDEO','LINK')),
  notas_publicacion         TEXT,
  created_at                TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 5: metricas
-- Métricas por publicación (captura manual MVP)
-- ============================================================
CREATE TABLE IF NOT EXISTS metricas (
  id                BIGSERIAL PRIMARY KEY,
  pub_id            BIGINT REFERENCES publicaciones(id) ON DELETE CASCADE,
  fecha_captura     DATE DEFAULT CURRENT_DATE,
  alcance           INTEGER DEFAULT 0,
  impresiones       INTEGER DEFAULT 0,
  reacciones        INTEGER DEFAULT 0,
  comentarios       INTEGER DEFAULT 0,
  compartidos       INTEGER DEFAULT 0,
  clics_link        INTEGER DEFAULT 0,
  guardados         INTEGER DEFAULT 0,
  engagement_rate   NUMERIC(5,2) GENERATED ALWAYS AS (
    CASE
      WHEN alcance > 0 THEN
        ROUND(((reacciones + comentarios + compartidos + guardados)::NUMERIC / alcance) * 100, 2)
      ELSE 0
    END
  ) STORED,
  score             INTEGER,
  clasificacion     TEXT CHECK (clasificacion IN ('GANADOR','PROMEDIO','PERDEDOR')),
  insight_ia        TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 6: prompts
-- Biblioteca de prompts versionados
-- ============================================================
CREATE TABLE IF NOT EXISTS prompts (
  id                    TEXT PRIMARY KEY, -- Ej: PRM-HOOK-01
  nombre                TEXT NOT NULL,
  categoria             TEXT CHECK (categoria IN ('HOOK','COPY','CTA','GUION','ANALISIS','REESCRITURA','INVESTIGACION','CARRUSEL','VIDEO')),
  version               INTEGER DEFAULT 1,
  prompt_text           TEXT NOT NULL,
  variables             TEXT, -- JSON string con lista de variables
  modelo_recomendado    TEXT DEFAULT 'gemini-1.5-pro',
  temperatura           NUMERIC(3,2) DEFAULT 0.7,
  ultima_edicion        DATE DEFAULT CURRENT_DATE,
  performance_notes     TEXT,
  activo                BOOLEAN DEFAULT TRUE,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 7: insights
-- Análisis semanales + recomendaciones
-- ============================================================
CREATE TABLE IF NOT EXISTS insights (
  id                        BIGSERIAL PRIMARY KEY,
  semana                    INTEGER NOT NULL,
  fecha_analisis            DATE DEFAULT CURRENT_DATE,
  top_post_id               BIGINT REFERENCES publicaciones(id) ON DELETE SET NULL,
  top_hook_tipo             TEXT,
  top_pilar                 TEXT,
  top_formato               TEXT,
  top_dolor                 TEXT,
  resumen_ia                TEXT,
  recomendacion_siguiente   TEXT,
  accion_tomada             TEXT,
  created_at                TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES para consultas frecuentes de n8n
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ideas_status         ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_ideas_score          ON ideas(score_potencial DESC);
CREATE INDEX IF NOT EXISTS idx_calendario_semana    ON calendario(semana);
CREATE INDEX IF NOT EXISTS idx_calendario_status    ON calendario(status);
CREATE INDEX IF NOT EXISTS idx_contenido_status     ON contenido(status);
CREATE INDEX IF NOT EXISTS idx_contenido_qa         ON contenido(qa_humanizacion);
CREATE INDEX IF NOT EXISTS idx_metricas_pub         ON metricas(pub_id);
CREATE INDEX IF NOT EXISTS idx_insights_semana      ON insights(semana);

-- ============================================================
-- VISTA: dashboard_semanal
-- Para el dashboard de métricas en n8n/Sheets
-- ============================================================
CREATE OR REPLACE VIEW dashboard_semanal AS
SELECT
  c.semana,
  COUNT(DISTINCT p.id)                          AS posts_publicados,
  AVG(m.engagement_rate)                        AS engagement_promedio,
  MAX(m.score)                                  AS mejor_score,
  MIN(m.score)                                  AS peor_score,
  SUM(m.alcance)                                AS alcance_total,
  SUM(m.reacciones)                             AS reacciones_total,
  SUM(m.compartidos)                            AS compartidos_total,
  SUM(m.comentarios)                            AS comentarios_total
FROM calendario c
JOIN contenido ct   ON ct.cal_id = c.id
JOIN publicaciones p ON p.content_id = ct.id
LEFT JOIN metricas m ON m.pub_id = p.id
GROUP BY c.semana
ORDER BY c.semana DESC;

-- ============================================================
-- VISTA: ideas_backlog
-- Ideas nuevas ordenadas por potencial (para WF-02)
-- ============================================================
CREATE OR REPLACE VIEW ideas_backlog AS
SELECT *
FROM ideas
WHERE status = 'NUEVA'
ORDER BY score_potencial DESC NULLS LAST, created_at DESC;

-- ============================================================
-- VISTA: contenido_por_aprobar
-- Borradores listos para revisión humana
-- ============================================================
CREATE OR REPLACE VIEW contenido_por_aprobar AS
SELECT
  ct.*,
  c.titulo_trabajo,
  c.fecha_publicacion,
  c.formato
FROM contenido ct
JOIN calendario c ON c.id = ct.cal_id
WHERE ct.status IN ('BORRADOR_IA', 'EDITADO_HUMANO')
ORDER BY c.fecha_publicacion ASC;

-- ============================================================
-- DATOS INICIALES: Prompts del sistema
-- ============================================================
INSERT INTO prompts (id, nombre, categoria, prompt_text, variables, temperatura) VALUES
(
  'PRM-HOOK-01',
  'Generador de Hooks Empáticos',
  'HOOK',
  'Eres la copywriter de Contexia. Tu tono es de amiga contadora: cercana, clara, empática, con criterio. Colombiana sin caricatura.

TEMA: {{tema}}
DOLOR QUE ATACA: {{dolor_icp}}
PILAR: {{pilar}}
FORMATO: {{formato}}

Genera 3 hooks diferentes. Cada hook debe capturar atención en menos de 3 segundos, máximo 120 caracteres.

Tipos de hook (uno diferente por opción):
1. Pregunta directa con dato
2. Afirmación contraintuitiva  
3. Empatía con dolor

Responde SOLO con este JSON:
{
  "hook_principal": "...",
  "hook_alt_1": "...",
  "hook_alt_2": "..."
}',
  '["tema","dolor_icp","pilar","formato"]',
  0.8
),
(
  'PRM-COPY-01',
  'Post Educativo Completo',
  'COPY',
  'Eres la voz de Contexia en Facebook. Escribe un post educativo.

HOOK (ya seleccionado): {{hook}}
TEMA: {{tema}}
ÁNGULO: {{angulo}}
DOLOR: {{dolor_icp}}

ESTRUCTURA: Hook → Contexto (1-2 oraciones) → Valor (explicación simple) → Acción (paso concreto) → CTA (invitar a interacción, no a venta)

REGLAS: máximo 300 palabras, párrafos cortos, usa "plata" no "recursos financieros", usa "la DIAN" naturalmente, máximo 3 emojis, no digas "en este post te voy a enseñar".

Responde SOLO con este JSON:
{
  "copy_body": "...",
  "cta": "...",
  "hashtags": "#Tag1 #Tag2 #Tag3"
}',
  '["hook","tema","angulo","dolor_icp"]',
  0.7
),
(
  'PRM-QA-01',
  'Detector de Tono Robótico',
  'REESCRITURA',
  'Eres el filtro de humanización de Contexia. Evalúa si este texto suena humano.

HOOK: {{hook}}
COPY: {{copy_body}}
CTA: {{cta}}

CHECKLIST:
1. ¿Suena como amiga que sabe, o como bot?
2. ¿Tiene palabras prohibidas? (revolucionario, potencializa, ecosistema, sinergia, maximizar)
3. ¿Tiene jerga contable opaca? (base gravable, causación, impuesto diferido)
4. ¿El CTA es protector o agresivo?
5. ¿Un emprendedor de 25 años lo entendería?

Responde SOLO con este JSON:
{
  "es_humano": true,
  "score_humanizacion": 8,
  "problemas": [],
  "version_reescrita": "solo si es_humano es false",
  "cambios_hechos": []
}',
  '["hook","copy_body","cta"]',
  0.3
),
(
  'PRM-RESEARCH-01',
  'Generador Semanal de Ideas',
  'INVESTIGACION',
  'Eres la estratega de contenidos de Contexia, una AI Automation Agency en Colombia especializada en Claridad Predictiva para PyMEs.

Dolores del ICP: miedo a la DIAN, desorden financiero, sorpresa tributaria, jerga opaca, ceguera de caja.
Patrones ganadores: {{patrones_ganadores}}
Recomendaciones previas: {{recomendaciones_previas}}

Genera exactamente 6 ideas de contenido para Facebook:
- 2 ideas del pilar CLARIDAD
- 2 ideas del pilar PROTECCION
- 1 idea del pilar ACCION
- 1 idea del pilar COMUNIDAD

Responde SOLO con este JSON array:
[
  {
    "tema": "título corto",
    "pilar": "CLARIDAD|PROTECCION|ACCION|COMUNIDAD",
    "formato_sugerido": "TEXTO_IMAGEN|CARRUSEL|VIDEO_CORTO|STORYTELLING",
    "dolor_icp": "MIEDO_DIAN|SORPRESA_TRIBUTARIA|DESORDEN|JERGA_OPACA|CEGUERA_CAJA|FORMALIZACION",
    "score_potencial": 8,
    "angulo": "ángulo específico para desarrollar"
  }
]',
  '["patrones_ganadores","recomendaciones_previas"]',
  0.8
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- DATOS INICIALES: Primera semana del calendario (mes 1)
-- ============================================================
INSERT INTO ideas (fecha_ingreso, fuente, tema_raw, pilar, angulo, formato_sugerido, dolor_icp, score_potencial, status) VALUES
(CURRENT_DATE, 'MANUAL', 'Qué es Contexia y por qué no somos contadores tradicionales', 'CLARIDAD', 'GPS financiero para emprendedores digitales', 'TEXTO_IMAGEN', 'JERGA_OPACA', 9, 'SELECCIONADA'),
(CURRENT_DATE, 'MANUAL', '3 cosas que la DIAN ya sabe de tu negocio digital', 'PROTECCION', 'La DIAN tiene acceso a tus movimientos bancarios y redes de pago', 'CARRUSEL', 'MIEDO_DIAN', 9, 'SELECCIONADA'),
(CURRENT_DATE, 'MANUAL', 'El mito de que la zona gris fiscal ya no existe para negocios online', 'PROTECCION', 'Toda transacción digital deja huella y la DIAN ya lo sabe', 'TEXTO_IMAGEN', 'MIEDO_DIAN', 8, 'NUEVA'),
(CURRENT_DATE, 'MANUAL', 'Cómo saber cuánto de lo que facturas es realmente tuyo', 'CLARIDAD', 'La diferencia entre ingreso y ganancia real', 'CARRUSEL', 'CEGUERA_CAJA', 9, 'NUEVA'),
(CURRENT_DATE, 'MANUAL', 'Caso: el emprendedor que facturó $15M pero solo $4M eran suyos', 'COMUNIDAD', 'Storytelling de caso real anonimizado de desorden financiero', 'STORYTELLING', 'CEGUERA_CAJA', 8, 'NUEVA'),
(CURRENT_DATE, 'MANUAL', '5 señales de que tu negocio digital necesita orden financiero hoy', 'ACCION', 'Checklist diagnóstico rápido de salud financiera', 'CARRUSEL', 'DESORDEN', 8, 'NUEVA')
ON CONFLICT DO NOTHING;

SELECT 'Schema creado exitosamente. Tablas: ideas, calendario, contenido, publicaciones, metricas, prompts, insights' AS resultado;
