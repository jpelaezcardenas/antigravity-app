-- Seed app_metadata.role for known users to support P0-4 cleanup.
-- After this, login.html + app-admin/index.html no longer need hardcoded email lists.
-- Run in AUTH project (kpynymwghfwshvcvevxq), NOT wizard project.

-- Admin
UPDATE auth.users
SET raw_app_meta_data = raw_app_meta_data || '{"role":"admin","roles":["admin"]}'::jsonb
WHERE email = 'contexia.marketing@gmail.com';

-- Clientes
UPDATE auth.users
SET raw_app_meta_data = raw_app_meta_data || '{"role":"cliente","roles":["cliente"]}'::jsonb
WHERE email IN ('growth@contexia.online', 'fperez@ferez.co');

-- Verify
SELECT email, raw_app_meta_data->'role' AS role
FROM auth.users
WHERE email IN (
  'contexia.marketing@gmail.com',
  'growth@contexia.online',
  'fperez@ferez.co'
)
ORDER BY email;
