import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"].strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

sql = open("migration.sql").read()

conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
conn.autocommit = True
cur = conn.cursor()

for statement in [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]:
    print(f"Running: {statement[:60]}...")
    cur.execute(statement)

# Fix the id sequence to prevent duplicate key errors
print("Fixing id sequence...")
cur.execute("SELECT setval('clubs_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM clubs))")

cur.close()
conn.close()
print("Migration complete.")
