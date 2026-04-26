# Configuración de Supabase para Contexia

Sigue estos pasos para preparar tu base de datos:

## 1. Tablas Necesarias

Ejecuta el script `supabase_schema.sql` en el SQL Editor de Supabase.

## 2. Autenticación

- Habilitar **Email/Password** en `Authentication > Providers`.
- Deshabilitar **Confirm Email** para pruebas rápidas (opcional).

## 3. Variables de Entorno

Obtén estas llaves desde `Project Settings > API`:
- `Project URL` -> `SUPABASE_URL`
- `anon public` key -> `SUPABASE_KEY`

Para el backend (Railway), necesitarás el connection string de la base de datos:
- `Project Settings > Database > Connection string > URI` -> `DATABASE_URL`

## 4. Políticas RLS (Row Level Security)

Asegúrate de que cada tabla tenga habilitado RLS y políticas que restrinjan el acceso solo al dueño del dato (`auth.uid()`).

```sql
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can see only their own profile" ON profiles 
FOR SELECT USING (auth.uid() = id);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can see only their own transactions" ON transactions 
FOR SELECT USING (auth.uid() = usuario_id);
```
