"""Run the DB migration for teacher_student_knowledge table."""
import os, re, sys
from dotenv import load_dotenv

load_dotenv()
import psycopg2

user     = os.getenv("POSTGRES_USER", "crafter_admin")
password = os.getenv("POSTGRES_PASSWORD", "")
host     = os.getenv("POSTGRES_HOST", "localhost")
port     = os.getenv("POSTGRES_PORT", "5432")
db       = os.getenv("POSTGRES_DB", "thecraftershub")

conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
conn.autocommit = True
cur = conn.cursor()

sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "01_teacher_student_knowledge.sql")
sql = open(sql_path).read()

# Execute the whole file at once
cur.execute(sql)
print("Migration executed successfully.")

cur.execute("SELECT COUNT(*) FROM teacher_student_knowledge")
print("Row count:", cur.fetchone()[0])

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='teacher_student_knowledge' ORDER BY ordinal_position")
cols = cur.fetchall()
print("Columns:", [c[0] for c in cols])

cur.close()
conn.close()
print("DONE.")
