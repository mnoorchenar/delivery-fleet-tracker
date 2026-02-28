from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3, os, math, time
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
# ProxyFix is required for HuggingFace Spaces (runs behind a reverse proxy)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.secret_key = os.environ.get("SECRET_KEY", "delivery-tracker-secret-2024")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

# DB lives next to app.py regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "delivery.db")

# ── Store HQ coordinates (Toronto) ────────────────────────────────────────────
STORE_LAT = 43.6532
STORE_LNG = -79.3832
STORE_NAME = "Main Warehouse"
DRIVER_SPEED_KMH = 35  # avg city speed

# ── Pre-defined destination pool for demo ─────────────────────────────────────
DEMO_DESTINATIONS = [
    {"name": "Pearson Airport",         "lat": 43.6777, "lng": -79.6248},
    {"name": "Scarborough Town Centre", "lat": 43.7764, "lng": -79.2318},
    {"name": "Etobicoke Civic Centre",  "lat": 43.6465, "lng": -79.5565},
    {"name": "North York Centre",       "lat": 43.7615, "lng": -79.4111},
    {"name": "Mississauga City Hall",   "lat": 43.5890, "lng": -79.6441},
    {"name": "Markham Civic Centre",    "lat": 43.8601, "lng": -79.3370},
    {"name": "Brampton Gateway",        "lat": 43.6855, "lng": -79.7598},
    {"name": "Ajax GO Station",         "lat": 43.8510, "lng": -79.0255},
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def interpolate(lat1, lng1, lat2, lng2, frac):
    frac = max(0.0, min(1.0, frac))
    return lat1 + (lat2-lat1)*frac, lng1 + (lng2-lng1)*frac

def eta_minutes(km):
    return round((km / DRIVER_SPEED_KMH) * 60, 1)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "manager":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated

# ── DB Init ────────────────────────────────────────────────────────────────────
def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL CHECK(role IN ('manager','driver'))
        );

        CREATE TABLE IF NOT EXISTS drivers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER UNIQUE REFERENCES users(id),
            name        TEXT NOT NULL,
            phone       TEXT DEFAULT '',
            vehicle     TEXT DEFAULT 'Van',
            status      TEXT DEFAULT 'idle'
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id    INTEGER REFERENCES drivers(id),
            package_id   TEXT NOT NULL,
            dest_name    TEXT NOT NULL,
            dest_lat     REAL NOT NULL,
            dest_lng     REAL NOT NULL,
            assigned_at  REAL NOT NULL,
            completed_at REAL,
            status       TEXT DEFAULT 'en_route'
                         CHECK(status IN ('en_route','at_destination','returning','completed','cancelled'))
        );
        """)

        # Always ensure default users exist (INSERT OR IGNORE is safe on re-runs)
        db.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('manager','manager','manager')")
        db.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('driver','driver','driver')")
        db.commit()

        # Ensure default driver profile exists
        drv_user = db.execute("SELECT id FROM users WHERE username='driver'").fetchone()
        if drv_user:
            db.execute("""INSERT OR IGNORE INTO drivers (user_id,name,phone,vehicle)
                          VALUES (?,?,?,?)""",
                       (drv_user["id"], "Alex Driver", "+1-416-555-0101", "Cargo Van"))
            db.commit()

        # Sanity check
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            raise RuntimeError("FATAL: init_db failed to create default users")

init_db()

# ── Auth Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("manager_dashboard" if session["role"] == "manager" else "driver_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                              (username, password)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("manager_dashboard" if user["role"]=="manager" else "driver_dashboard"))
        error = "Invalid credentials."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Manager Dashboard ──────────────────────────────────────────────────────────
@app.route("/manager")
@login_required
def manager_dashboard():
    if session["role"] != "manager":
        return redirect(url_for("driver_dashboard"))
    with get_db() as db:
        drivers = db.execute("""
            SELECT d.id, d.name, d.phone, d.vehicle, d.status,
                   u.username
            FROM drivers d JOIN users u ON d.user_id=u.id
        """).fetchall()
    return render_template("manager.html",
                           drivers=[dict(r) for r in drivers],
                           destinations=DEMO_DESTINATIONS,
                           store={"lat": STORE_LAT, "lng": STORE_LNG, "name": STORE_NAME})

# ── Driver Dashboard ───────────────────────────────────────────────────────────
@app.route("/driver")
@login_required
def driver_dashboard():
    if session["role"] != "driver":
        return redirect(url_for("manager_dashboard"))
    with get_db() as db:
        driver = db.execute("SELECT * FROM drivers WHERE user_id=?", (session["user_id"],)).fetchone()
    if not driver:
        return "Driver profile not found.", 404
    return render_template("driver.html",
                           driver=dict(driver),
                           store={"lat": STORE_LAT, "lng": STORE_LNG, "name": STORE_NAME})

# ── Manager: Register new driver ───────────────────────────────────────────────
@app.route("/api/register_driver", methods=["POST"])
@login_required
def register_driver():
    if session["role"] != "manager":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    name     = data.get("name","").strip()
    phone    = data.get("phone","").strip()
    vehicle  = data.get("vehicle","Van").strip()
    if not username or not password or not name:
        return jsonify({"error": "username, password, name are required"}), 400
    try:
        with get_db() as db:
            db.execute("INSERT INTO users (username,password,role) VALUES (?,?,'driver')", (username, password))
            uid = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]
            db.execute("INSERT INTO drivers (user_id,name,phone,vehicle) VALUES (?,?,?,?)",
                       (uid, name, phone, vehicle))
            db.commit()
        return jsonify({"success": True, "message": f"Driver '{name}' registered."})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

# ── Manager: Assign delivery ───────────────────────────────────────────────────
@app.route("/api/assign", methods=["POST"])
@login_required
def assign_delivery():
    if session["role"] != "manager":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    driver_id  = data.get("driver_id")
    dest_name  = data.get("dest_name","").strip()
    dest_lat   = float(data.get("dest_lat", 0))
    dest_lng   = float(data.get("dest_lng", 0))
    package_id = data.get("package_id", f"PKG-{int(time.time())}")

    if not driver_id or not dest_name:
        return jsonify({"error": "driver_id and dest_name required"}), 400

    with get_db() as db:
        # Cancel any active delivery for this driver
        db.execute("""UPDATE deliveries SET status='cancelled'
                      WHERE driver_id=? AND status IN ('en_route','at_destination','returning')""",
                   (driver_id,))
        db.execute("""INSERT INTO deliveries
                      (driver_id, package_id, dest_name, dest_lat, dest_lng, assigned_at, status)
                      VALUES (?,?,?,?,?,?,'en_route')""",
                   (driver_id, package_id, dest_name, dest_lat, dest_lng, time.time()))
        db.execute("UPDATE drivers SET status='busy' WHERE id=?", (driver_id,))
        db.commit()

    dist_km = haversine_km(STORE_LAT, STORE_LNG, dest_lat, dest_lng)
    return jsonify({"success": True,
                    "message": f"Assigned {package_id} to driver {driver_id}",
                    "eta_to_dest_min": eta_minutes(dist_km),
                    "distance_km": round(dist_km, 2)})

# ── API: Live driver positions (manager only) ──────────────────────────────────
@app.route("/api/drivers/live")
@login_required
def drivers_live():
    if session["role"] != "manager":
        return jsonify({"error": "Unauthorized"}), 403

    now = time.time()
    results = []

    with get_db() as db:
        drivers = db.execute("""
            SELECT d.id, d.name, d.vehicle, d.status,
                   u.username
            FROM drivers d JOIN users u ON d.user_id=u.id
        """).fetchall()

        for drv in drivers:
            drv = dict(drv)
            delivery = db.execute("""
                SELECT * FROM deliveries
                WHERE driver_id=? AND status IN ('en_route','at_destination','returning')
                ORDER BY assigned_at DESC LIMIT 1
            """, (drv["id"],)).fetchone()

            if not delivery:
                drv["lat"] = STORE_LAT
                drv["lng"] = STORE_LNG
                drv["delivery"] = None
                drv["status_label"] = "Idle at Warehouse"
                drv["eta_min"] = None
                results.append(drv)
                continue

            delivery = dict(delivery)
            dlat, dlng = delivery["dest_lat"], delivery["dest_lng"]
            dist_to_dest = haversine_km(STORE_LAT, STORE_LNG, dlat, dlng)
            speed_km_s = DRIVER_SPEED_KMH / 3600
            travel_time_s = (dist_to_dest / speed_km_s)
            dwell_s = 30  # seconds at destination

            elapsed = now - delivery["assigned_at"]
            total_trip_s = travel_time_s * 2 + dwell_s

            if elapsed < travel_time_s:
                # En route to destination
                frac = elapsed / travel_time_s
                lat, lng = interpolate(STORE_LAT, STORE_LNG, dlat, dlng, frac)
                remain_s = travel_time_s - elapsed
                eta_str = str(timedelta(seconds=int(remain_s))).split(".")[0]
                status_label = f"En route to {delivery['dest_name']}"
                delivery_status = "en_route"
                # Update DB if needed
                if delivery["status"] != "en_route":
                    db.execute("UPDATE deliveries SET status='en_route' WHERE id=?", (delivery["id"],))
                    db.commit()

            elif elapsed < travel_time_s + dwell_s:
                # At destination
                lat, lng = dlat, dlng
                remain_s = (travel_time_s + dwell_s) - elapsed
                eta_str = f"Returning in {int(remain_s)}s"
                status_label = f"At {delivery['dest_name']}"
                delivery_status = "at_destination"
                if delivery["status"] != "at_destination":
                    db.execute("UPDATE deliveries SET status='at_destination' WHERE id=?", (delivery["id"],))
                    db.commit()

            elif elapsed < total_trip_s:
                # Returning to store
                frac = (elapsed - travel_time_s - dwell_s) / travel_time_s
                lat, lng = interpolate(dlat, dlng, STORE_LAT, STORE_LNG, frac)
                remain_s = total_trip_s - elapsed
                eta_str = str(timedelta(seconds=int(remain_s))).split(".")[0]
                status_label = f"Returning to {STORE_NAME}"
                delivery_status = "returning"
                if delivery["status"] != "returning":
                    db.execute("UPDATE deliveries SET status='returning' WHERE id=?", (delivery["id"],))
                    db.commit()

            else:
                # Trip complete
                lat, lng = STORE_LAT, STORE_LNG
                eta_str = "Arrived"
                status_label = "Idle at Warehouse"
                delivery_status = "completed"
                if delivery["status"] != "completed":
                    db.execute("UPDATE deliveries SET status='completed', completed_at=? WHERE id=?",
                               (now, delivery["id"]))
                    db.execute("UPDATE drivers SET status='idle' WHERE id=?", (drv["id"],))
                    db.commit()

            drv["lat"] = round(lat, 6)
            drv["lng"] = round(lng, 6)
            drv["status_label"] = status_label
            drv["eta_str"] = eta_str
            drv["delivery"] = {
                "id": delivery["id"],
                "package_id": delivery["package_id"],
                "dest_name": delivery["dest_name"],
                "dest_lat": dlat,
                "dest_lng": dlng,
                "status": delivery_status,
                "assigned_at": delivery["assigned_at"],
                "dist_km": round(dist_to_dest, 2),
            }
            results.append(drv)

    return jsonify({"store": {"lat": STORE_LAT, "lng": STORE_LNG, "name": STORE_NAME},
                    "drivers": results, "timestamp": now})

# ── API: Driver's own status ───────────────────────────────────────────────────
@app.route("/api/my_status")
@login_required
def my_status():
    if session["role"] != "driver":
        return jsonify({"error": "Not a driver"}), 400

    now = time.time()
    with get_db() as db:
        drv = db.execute("SELECT * FROM drivers WHERE user_id=?", (session["user_id"],)).fetchone()
        if not drv:
            return jsonify({"error": "Driver not found"}), 404
        drv = dict(drv)

        delivery = db.execute("""
            SELECT * FROM deliveries
            WHERE driver_id=? AND status IN ('en_route','at_destination','returning')
            ORDER BY assigned_at DESC LIMIT 1
        """, (drv["id"],)).fetchone()

    if not delivery:
        return jsonify({
            "status": "idle",
            "status_label": "Waiting for assignment",
            "lat": STORE_LAT, "lng": STORE_LNG,
            "delivery": None
        })

    delivery = dict(delivery)
    dlat, dlng = delivery["dest_lat"], delivery["dest_lng"]
    dist_to_dest = haversine_km(STORE_LAT, STORE_LNG, dlat, dlng)
    speed_km_s = DRIVER_SPEED_KMH / 3600
    travel_time_s = dist_to_dest / speed_km_s
    dwell_s = 30
    elapsed = now - delivery["assigned_at"]
    total_trip_s = travel_time_s * 2 + dwell_s

    if elapsed < travel_time_s:
        frac = elapsed / travel_time_s
        lat, lng = interpolate(STORE_LAT, STORE_LNG, dlat, dlng, frac)
        remain_s = travel_time_s - elapsed
        status = "en_route"
        status_label = f"En route → {delivery['dest_name']}"
        eta_dest = str(timedelta(seconds=int(remain_s))).split(".")[0]
        eta_store = str(timedelta(seconds=int(remain_s + dwell_s + travel_time_s))).split(".")[0]
    elif elapsed < travel_time_s + dwell_s:
        lat, lng = dlat, dlng
        remain_s = (travel_time_s + dwell_s) - elapsed
        status = "at_destination"
        status_label = f"📦 Delivering at {delivery['dest_name']}"
        eta_dest = "Arrived!"
        eta_store = str(timedelta(seconds=int(remain_s + travel_time_s))).split(".")[0]
    elif elapsed < total_trip_s:
        frac = (elapsed - travel_time_s - dwell_s) / travel_time_s
        lat, lng = interpolate(dlat, dlng, STORE_LAT, STORE_LNG, frac)
        remain_s = total_trip_s - elapsed
        status = "returning"
        status_label = f"Returning → {STORE_NAME}"
        eta_dest = "Delivered ✓"
        eta_store = str(timedelta(seconds=int(remain_s))).split(".")[0]
    else:
        lat, lng = STORE_LAT, STORE_LNG
        status = "completed"
        status_label = "Back at Warehouse"
        eta_dest = "Delivered ✓"
        eta_store = "Arrived ✓"

    progress_pct = min(100, int((elapsed / total_trip_s) * 100)) if total_trip_s > 0 else 0

    return jsonify({
        "status": status,
        "status_label": status_label,
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "eta_to_dest": eta_dest,
        "eta_to_store": eta_store,
        "progress_pct": progress_pct,
        "delivery": {
            "package_id": delivery["package_id"],
            "dest_name": delivery["dest_name"],
            "dest_lat": dlat,
            "dest_lng": dlng,
            "dist_km": round(dist_to_dest, 2),
            "status": status,
        }
    })

# ── Manager: Delivery history ──────────────────────────────────────────────────
@app.route("/api/history")
@login_required
def delivery_history():
    if session["role"] != "manager":
        return jsonify({"error": "Unauthorized"}), 403
    with get_db() as db:
        rows = db.execute("""
            SELECT dl.*, d.name as driver_name
            FROM deliveries dl JOIN drivers d ON dl.driver_id=d.id
            ORDER BY dl.assigned_at DESC LIMIT 50
        """).fetchall()
    return jsonify({"history": [dict(r) for r in rows]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)
