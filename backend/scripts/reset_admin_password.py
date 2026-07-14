import sqlite3
import bcrypt
import secrets
import string
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).parent.parent / 'cloudvault.db'
TARGET_EMAIL = 'drish@example.com'  # admin account to reset

# Generate a secure random password
alphabet = string.ascii_letters + string.digits
new_password = ''.join(secrets.choice(alphabet) for _ in range(16))

if not DB_PATH.exists():
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

try:
    # Hash password using bcrypt to match application
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cur.execute('UPDATE users SET hashed_password = ? WHERE email = ?', (hashed, TARGET_EMAIL))
    if cur.rowcount == 0:
        print('No user found with email', TARGET_EMAIL)
        conn.rollback()
    else:
        conn.commit()
        print('Password reset successful for', TARGET_EMAIL)
        print('NEW_PASSWORD:' , new_password)
finally:
    conn.close()
