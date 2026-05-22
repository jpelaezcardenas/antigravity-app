-- Schema para Contexia

-- 1. Perfiles de Usuario (Ligados a Auth)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  nombre_empresa TEXT NOT NULL,
  nit TEXT,
  plan TEXT DEFAULT 'starter',
  porcentaje_renta FLOAT DEFAULT 0.35,
  porcentaje_iva FLOAT DEFAULT 0.19,
  activo BOOLEAN DEFAULT True,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Transacciones Financieras
CREATE TABLE IF NOT EXISTS transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  usuario_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  fecha DATE NOT NULL,
  tipo TEXT CHECK (tipo IN ('ingreso', 'gasto')) NOT NULL,
  monto FLOAT NOT NULL,
  concepto TEXT,
  categoria TEXT DEFAULT 'general',
  origen TEXT DEFAULT 'manual',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Alertas Fiscales
CREATE TABLE IF NOT EXISTS tax_alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  usuario_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  tipo TEXT NOT NULL,
  severidad TEXT NOT NULL,
  titulo TEXT NOT NULL,
  descripcion TEXT,
  accion_sugerida TEXT,
  fecha_limite DATE,
  activa BOOLEAN DEFAULT True,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Trigger para crear perfil automáticamente al registrarse
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, nombre_empresa)
  VALUES (new.id, new.email, 'Mi Empresa');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
-- CREATE TRIGGER on_auth_user_created
--   AFTER INSERT ON auth.users
--   FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();


-- ============================================================================
-- 4. Social Content Ops - Campaign Management & Post Scheduling
-- ============================================================================

CREATE TABLE IF NOT EXISTS social_campaigns (
  id TEXT DEFAULT gen_random_uuid()::text PRIMARY KEY,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  tipo TEXT CHECK (tipo IN ('discovery', 'engagement', 'conversion', 'retention')) DEFAULT 'discovery',
  estado TEXT CHECK (estado IN ('activa', 'pausada', 'finalizada')) DEFAULT 'activa',
  presupuesto FLOAT DEFAULT 0,
  presupuesto_usado FLOAT DEFAULT 0,
  fecha_inicio DATE,
  fecha_fin DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS social_posts (
  id TEXT DEFAULT gen_random_uuid()::text PRIMARY KEY,
  campaign_id TEXT REFERENCES social_campaigns(id) ON DELETE CASCADE NOT NULL,
  titulo TEXT NOT NULL,
  contenido TEXT NOT NULL,
  plataforma TEXT CHECK (plataforma IN ('facebook', 'instagram', 'tiktok', 'general')) NOT NULL,
  hashtags TEXT[] DEFAULT ARRAY[]::TEXT[],
  estado TEXT CHECK (estado IN ('borrador', 'programado', 'publicado', 'fallido')) DEFAULT 'borrador',
  fecha_programada DATE,
  hora_programada TIME,
  fecha_publicacion TIMESTAMP WITH TIME ZONE,
  costo_produccion FLOAT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS social_post_metrics (
  id TEXT DEFAULT gen_random_uuid()::text PRIMARY KEY,
  post_id TEXT REFERENCES social_posts(id) ON DELETE CASCADE NOT NULL,
  impressions BIGINT DEFAULT 0,
  reach BIGINT DEFAULT 0,
  engagement BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  shares BIGINT DEFAULT 0,
  comentarios BIGINT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS content_library (
  id TEXT DEFAULT gen_random_uuid()::text PRIMARY KEY,
  titulo TEXT NOT NULL,
  tipo TEXT CHECK (tipo IN ('post', 'template', 'guia')) NOT NULL,
  plataforma TEXT CHECK (plataforma IN ('facebook', 'instagram', 'tiktok', 'general')) NOT NULL,
  contenido TEXT,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  usos_totales BIGINT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for performance
CREATE INDEX idx_posts_campaign_id ON social_posts(campaign_id);
CREATE INDEX idx_posts_estado ON social_posts(estado);
CREATE INDEX idx_posts_fecha_programada ON social_posts(fecha_programada);
CREATE INDEX idx_metrics_post_id ON social_post_metrics(post_id);
CREATE INDEX idx_content_tipo ON content_library(tipo);
CREATE INDEX idx_campaigns_estado ON social_campaigns(estado);
