import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')
db_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

with open('../../supabase_schema.sql', 'r', encoding='utf-8') as f:
    schema_sql = f.read()

print('Running schema...')
cur.execute(schema_sql)

print('Inserting admin and client users...')
cur.execute("""
INSERT INTO usuarios (id, email, nombre_empresa, nit, password_hash, plan)
VALUES
(gen_random_uuid(), 'admin@contexia.co', 'Contexia Admin', '000000000-0', '$2b$12$placeholder_hash_para_demo', 'enterprise'),
(gen_random_uuid(), 'cliente@demo.co', 'Empresa Cliente Demo', '111111111-1', '$2b$12$placeholder_hash_para_demo', 'starter'),
(gen_random_uuid(), 'contexia.marketing@gmail.com', 'Contexia', '1017195431', '$2b$12$placeholder_hash_para_demo', 'enterprise')
ON CONFLICT (email) DO NOTHING;
""")

print('Done.')
