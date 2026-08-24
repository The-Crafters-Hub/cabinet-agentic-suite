import sys; sys.path.insert(0, '.')
from db.connection import get_connection

with get_connection() as conn:
    conn.autocommit = True
    with conn.cursor() as cur:
        sql = open('db/migrations/02_fix_embedding_dim.sql').read()
        cur.execute(sql)
        print('Migration 02 applied OK')
        cur.execute("SELECT atttypmod FROM pg_attribute pa JOIN pg_class pc ON pc.oid = pa.attrelid WHERE pc.relname='teacher_student_knowledge' AND pa.attname='embedding'")
        r2 = cur.fetchone()
        print('Column atttypmod (dims+1):', r2[0] if r2 else 'unknown')
