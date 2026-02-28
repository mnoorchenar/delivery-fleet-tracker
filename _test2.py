import os, sqlite3, traceback

os.chdir(r"E:\HuggingFace\delivery-fleet-tracker")
DB = os.path.join(os.getcwd(), "delivery.db")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

try:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role     TEXT NOT NULL CHECK(role IN ('manager','driver'))
    );
    CREATE TABLE IF NOT EXISTS drivers (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id),
        name    TEXT NOT NULL,
        phone   TEXT DEFAULT '',
        vehicle TEXT DEFAULT 'Van',
        status  TEXT DEFAULT 'idle'
    );
    """)
    print("executescript OK")
except Exception as e:
    print("executescript ERROR:", e)
    traceback.print_exc()

# Try the insert
try:
    conn.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('manager','manager','manager')")
    conn.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('driver','driver','driver')")
    conn.commit()
    print("inserts OK")
except Exception as e:
    print("insert ERROR:", e)
    traceback.print_exc()

users = conn.execute("SELECT * FROM users").fetchall()
print("Users:", [dict(u) for u in users])
conn.close()
