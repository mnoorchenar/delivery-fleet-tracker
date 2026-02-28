import os, sqlite3

os.chdir(r"E:\HuggingFace\delivery-fleet-tracker")
DB = os.path.join(os.getcwd(), "delivery.db")
print("DB path:", DB)
print("DB exists:", os.path.exists(DB))

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t["name"] for t in tables])

try:
    users = conn.execute("SELECT id, username, password, role FROM users").fetchall()
    print("Users in DB:")
    for u in users:
        print("  ", dict(u))
    
    # Test login query
    for creds in [("manager","manager"), ("driver","driver")]:
        found = conn.execute("SELECT * FROM users WHERE username=? AND password=?", creds).fetchone()
        print(f"Login {creds[0]}/{creds[1]}:", "OK" if found else "FAIL")
except Exception as e:
    print("ERROR:", e)

conn.close()
