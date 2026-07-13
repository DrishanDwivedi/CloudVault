import sqlite3
from pathlib import Path
p=Path(__file__).parent / 'cloudvault.db'
if not p.exists():
    print('DB not found at', p)
    raise SystemExit(0)
conn=sqlite3.connect(str(p))
cur=conn.cursor()
try:
    cur.execute("SELECT id, email, role, is_active, created_at FROM users")
    rows=cur.fetchall()
    if not rows:
        print('No users found in DB')
    else:
        for r in rows:
            print(f'id={r[0]}, email={r[1]}, role={r[2]}, is_active={r[3]}, created_at={r[4]}')
except Exception as e:
    print('Query failed:', e)
finally:
    conn.close()
