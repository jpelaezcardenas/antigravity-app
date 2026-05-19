-- Esquema de Base de Datos para Contexia
-- Ejecutar en el SQL Editor de Supabase

-- 1. Usuarios / Empresas
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    email TEXT UNIQUE NOT NULL,
    nombre_empresa TEXT NOT NULL,
    nit TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'starter',
    porcentaje_renta FLOAT DEFAULT 0.35,
    porcentaje_iva FLOAT DEFAULT 0.19,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 2. Transacciones (Sincronizadas de Siigo/Stripe/etc)
CREATE TABLE IF NOT EXISTS transacciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id),
    fecha DATE NOT NULL,
    tipo TEXT CHECK (tipo IN ('ingreso', 'gasto')),
    monto DECIMAL(15,2) NOT NULL,
    concepto TEXT,
    categoria TEXT,
    origen TEXT DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 3. Alertas Fiscales (Centinela)
CREATE TABLE IF NOT EXISTS alertas_fiscales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id),
    tipo TEXT NOT NULL,
    severidad TEXT NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    accion_sugerida TEXT,
    fecha_limite DATE,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 4. Facturas Vencidas (Asistente de Cobro)
CREATE TABLE IF NOT EXISTS facturas_vencidas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id),
    numero_factura TEXT NOT NULL,
    cliente TEXT NOT NULL,
    monto DECIMAL(15,2) NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado TEXT DEFAULT 'no_pagada',
    intentos_cobro INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 5. Eventos de Cobro (Bitácora)
CREATE TABLE IF NOT EXISTS eventos_cobro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factura_id UUID REFERENCES facturas_vencidas(id),
    usuario_id UUID REFERENCES usuarios(id),
    tipo_evento TEXT NOT NULL, -- 'recordatorio_enviado', 'llamada', etc
    resultado TEXT,
    monto_comprometido DECIMAL(15,2),
    fecha_pago_comprometida DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Habilitar RLS (Row Level Security)
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas_fiscales ENABLE ROW LEVEL SECURITY;
ALTER TABLE facturas_vencidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_cobro ENABLE ROW LEVEL SECURITY;

-- Políticas básicas (El usuario solo ve sus datos)
CREATE POLICY "Usuarios pueden ver sus propios datos" ON usuarios FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Usuarios pueden ver sus transacciones" ON transacciones FOR ALL USING (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden ver sus alertas" ON alertas_fiscales FOR ALL USING (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden ver sus facturas" ON facturas_vencidas FOR ALL USING (auth.uid() = usuario_id);
CREATE POLICY "Usuarios pueden ver sus eventos de cobro" ON eventos_cobro FOR ALL USING (auth.uid() = usuario_id);

-- Datos de Prueba para Demo
INSERT INTO usuarios (id, email, nombre_empresa, nit, password_hash)
VALUES 
('d17d4a70-7b5e-4b4e-9b4e-123456789012', 'lavaderos_ld@contexia.com', 'Lavaderos LD', '123456789-1', '$2b$12$placeholder_hash_para_demo'),
('e28e5b81-8c6f-5c5f-0c5f-234567890123', 'sion@contexia.com', 'Sion Estrategia', '234567890-2', '$2b$12$placeholder_hash_para_demo'),
('f39f6c92-9d7g-6d6g-1d6g-345678901234', 'repuestos_don_alvaro@contexia.com', 'Repuestos Don Alvaro', '345678901-3', '$2b$12$placeholder_hash_para_demo')
ON CONFLICT (email) DO NOTHING;
