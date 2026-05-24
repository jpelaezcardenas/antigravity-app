import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
cur = conn.cursor()
cur.execute("UPDATE usuarios SET password_hash='$2b$12$placeholder_hash_para_demo' WHERE email='contexia.marketing@gmail.com'")
print("Updated hash for contexia.marketing@gmail.com")
