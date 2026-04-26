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
