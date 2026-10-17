---
title: delivery-fleet-tracker
colorFrom: yellow
colorTo: blue
sdk: docker
---

<div align="center">

<h1>🚚 DeliveryOS — Fleet Tracking System</h1>
<img src="https://readme-typing-svg.demolab.com?font=Space+Mono&size=20&duration=3000&pause=1000&color=F59E0B&center=true&vCenter=true&width=700&lines=Real-Time+Delivery+Fleet+Tracking;London+Ontario+%7C+50+km+Coverage;Manager+Dashboard+%7C+Driver+Portal;Dispatch+%7C+Cancel+%7C+KPIs+%7C+History" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-4f46e5?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-22c55e?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-3b82f6?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)](#)

<br/>

[![Live Demo](https://img.shields.io/badge/%E2%96%B6_Live_Demo-Hugging_Face_Space-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/mnoorchenar/delivery-fleet-tracker)
[![Source Code](https://img.shields.io/badge/Source_Code-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mnoorchenar/delivery-fleet-tracker)

<br/>

**🚚 DeliveryOS** is a full-stack delivery fleet management system for **London, Ontario and the surrounding 50 km area**. Packages are dispatched to drivers, their GPS position is simulated along the route (warehouse → destination → warehouse), and the manager dashboard auto-refreshes every 5 seconds — no page reload needed.

<br/>

---

</div>

## Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Getting Started](#-getting-started)
- [Docker Deployment](#-docker-deployment)
- [Configuration](#️-configuration)
- [Dashboard Modules](#-dashboard-modules)
- [Simulation Logic](#-simulation-logic)
- [API Reference](#-api-reference)
- [Default Credentials](#-default-credentials)
- [Project Structure](#-project-structure)
- [Author](#-author)
- [Contributing](#-contributing)
- [Disclaimer](#️-disclaimer)
- [License](#-license)

---

## ✨ Features

<table>
  <tr>
    <td>⚡ <b>WebSocket Push Updates</b></td>
    <td>Manager dashboard receives live fleet state every 4 seconds via Flask-SocketIO — no polling lag. Automatically falls back to 10s REST polling if WebSocket is unavailable.</td>
  </tr>
  <tr>
    <td>🗺️ <b>Live Fleet Map</b></td>
    <td>Interactive Leaflet.js map (OpenStreetMap, no API key) showing all driver positions, dashed full-route lines, and live driver-to-target lines that update in real time.</td>
  </tr>
  <tr>
    <td>⏱️ <b>ETA Engine</b></td>
    <td>Haversine distance + linear interpolation at a configurable city speed. Separate ETAs to destination and back to warehouse update continuously on both manager and driver views.</td>
  </tr>
  <tr>
    <td>📊 <b>KPI Stats Bar</b></td>
    <td>Manager dashboard shows four live counters: Active deliveries, Idle drivers, Deliveries completed today, and Average delivery time (minutes).</td>
  </tr>
  <tr>
    <td>✅ <b>Completion Notifications</b></td>
    <td>When any driver completes a delivery, the manager sees a green toast alert and a persistent badge counter in the nav — no need to watch the map.</td>
  </tr>
  <tr>
    <td>❌ <b>Delivery Cancellation</b></td>
    <td>Manager can cancel any active delivery directly from the driver card or the history tab. The driver is immediately freed and marked idle.</td>
  </tr>
  <tr>
    <td>📜 <b>Filterable History</b></td>
    <td>Delivery history tab filters live by driver name and status. Active deliveries in the history list also show a cancel button.</td>
  </tr>
  <tr>
    <td>📦 <b>Smart Package IDs</b></td>
    <td>Auto-generated IDs follow the <code>PKG-YYMMDD-NNNN</code> format (e.g. <code>PKG-260329-0003</code>). Custom IDs are still accepted.</td>
  </tr>
  <tr>
    <td>🔍 <b>Address Search</b></td>
    <td>Free Nominatim geocoding with a live loading indicator and network-error feedback. No Google Maps API key required.</td>
  </tr>
  <tr>
    <td>👤 <b>Driver Registration</b></td>
    <td>Manager registers new drivers in-app. The assign dropdown refreshes automatically via AJAX — no page reload needed.</td>
  </tr>
  <tr>
    <td>🚚 <b>Driver History & Stats</b></td>
    <td>Each driver sees their last 20 deliveries with distance, duration, and status, plus lifetime and today delivery counts at the top of their dashboard.</td>
  </tr>
  <tr>
    <td>🔒 <b>Secure Auth</b></td>
    <td>Passwords hashed with werkzeug scrypt. Session secret loaded from the <code>SECRET_KEY</code> environment variable. Role-based access on every route and WebSocket connection.</td>
  </tr>
  <tr>
    <td>🐳 <b>Containerized</b></td>
    <td>Docker-first, Hugging Face Spaces-ready on port 7860. SQLite auto-falls back to <code>/tmp</code> if <code>/app/data</code> is not writable. Warehouse location fully configurable via env vars.</td>
  </tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DeliveryOS                                  │
│                                                                      │
│  ┌────────────┐    ┌──────────────────────────────┐    ┌──────────┐ │
│  │  SQLite DB │───▶│           Flask               │───▶│ Jinja2   │ │
│  │  users     │    │  routes · simulation engine   │    │ Leaflet  │ │
│  │  drivers   │    │  _build_fleet_payload()        │    │ Vanilla  │ │
│  │  deliveries│    │                               │    │   JS     │ │
│  └────────────┘    └──────────────────────────────┘    └──────────┘ │
│                              │                                       │
│              ┌───────────────┴───────────────────────────┐          │
│              │  REST polling (every 5s)                  │          │
│              │  GET /api/drivers/live  GET /api/my_status │          │
│              └───────────────────────────────────────────┘          │
│                                                                      │
│  Manager Dashboard ◀── 5s poll ── Server ── 5s poll ──▶ Driver      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- Single gunicorn worker (pure Python, no C extensions) for fast Docker builds
- Server-side simulation: position computed on-demand from `assigned_at` timestamp — no background GPS thread needed
- All state in SQLite; server restarts are safe
- Zero external paid APIs: OpenStreetMap tiles + Nominatim geocoding

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Git

### Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/mnoorchenar/delivery-fleet-tracker.git
cd delivery-fleet-tracker

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) set a strong secret key
export SECRET_KEY="your-secret-key-here"

# 5. Run the application
python app.py
```

Open `http://localhost:7860` in your browser.

> **Note:** On first run, the database is created automatically with default users and the demo driver profile.

---

## 🐳 Docker Deployment

```bash
# Build and run
docker build -t delivery-fleet-tracker .
docker run -p 7860:7860 \
  -e SECRET_KEY="your-secret" \
  -e STORE_NAME="My Warehouse" \
  -v $(pwd)/data:/app/data \
  delivery-fleet-tracker
```

For **Hugging Face Spaces**, set `SECRET_KEY` (and any other vars) in your Space's **Settings → Repository secrets** panel. The app detects the `SPACE_ID` environment variable automatically and configures cookies for the HF iframe environment.

---

## ⚙️ Configuration

All configuration is done via environment variables. No config files to edit.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `delivery-os-dev-fallback-change-me` | Flask session secret — **always set in production** |
| `STORE_LAT` | `43.6532` | Warehouse latitude |
| `STORE_LNG` | `-79.3832` | Warehouse longitude |
| `STORE_NAME` | `Main Warehouse` | Warehouse display name |
| `DRIVER_SPEED_KMH` | `35` | Simulated average city speed |
| `DB_PATH` | `./data/delivery.db` | SQLite database path |
| `GOOGLE_MAPS_KEY` | _(empty)_ | Optional — only used for "Navigate" deep links |

Example for a different city:

```bash
export STORE_LAT=51.5074
export STORE_LNG=-0.1278
export STORE_NAME="London Depot"
export SECRET_KEY="change-me-in-production"
python app.py
```

---

## 📊 Dashboard Modules

### Manager Dashboard

| Module | Description |
|--------|-------------|
| 🗺️ **Live Fleet Map** | Real-time driver markers, destination pins, dashed full-route lines, live driver-to-target lines |
| 📊 **KPI Stats Bar** | Active · Idle · Today · Avg Min — updated with every WebSocket push |
| 🔔 **Completion Alerts** | Green toast + nav badge counter fires when any delivery completes |
| 📋 **Driver Fleet List** | Scrollable driver cards with status, ETA, Google Maps link, and cancel button |
| 📦 **Dispatch Panel** | Driver selector, Nominatim address search with live spinner, package ID field, dispatch button with loading state |
| 👤 **Driver Registration** | In-app form; assign dropdown auto-refreshes on success via AJAX |
| 📜 **Delivery History** | Last 100 deliveries, filtered live by driver name and status; active entries show a cancel button |

### Driver Dashboard

| Module | Description |
|--------|-------------|
| 📈 **Stats Bar** | Lifetime trip count and today's count |
| 🎯 **Status Hero** | Phase icon and label (En Route / At Destination / Returning / Idle) |
| 📏 **Trip Progress** | Animated progress bar with warehouse → destination → warehouse stops |
| ⏱️ **ETA Cards** | Separate ETAs to destination and back to warehouse |
| 📦 **Package Detail** | Package ID, destination, distance, vehicle type, Google Maps navigation link |
| 📜 **My Deliveries** | Last 20 personal deliveries with date, distance, duration, and status badge; auto-refreshes on return to idle |

---

## 🧮 Simulation Logic

GPS simulation runs entirely server-side — no background jobs, no external services.

```python
# When /api/drivers/live is called (or the broadcast task fires):
elapsed = now - delivery["assigned_at"]   # seconds since dispatch

if elapsed < travel_s:                    # Phase 1: en_route
    frac = elapsed / travel_s
    lat, lng = lerp(STORE, DEST, frac)

elif elapsed < travel_s + DWELL_S:        # Phase 2: at_destination (30s)
    lat, lng = DEST

elif elapsed < travel_s * 2 + DWELL_S:   # Phase 3: returning
    frac = (elapsed - travel_s - DWELL_S) / travel_s
    lat, lng = lerp(DEST, STORE, frac)

else:                                     # Phase 4: completed
    lat, lng = STORE
```

| Parameter | Value |
|-----------|-------|
| Speed | 35 km/h (configurable via `DRIVER_SPEED_KMH`) |
| Distance formula | Haversine (spherical Earth) |
| Position interpolation | Linear (great-circle blend) |
| Dwell time at destination | 30 seconds |
| Push interval | 4 seconds (WebSocket) |
| Fallback poll interval | 10 seconds (REST) |

---

## 📡 API Reference

All endpoints require a valid session cookie. Manager-only endpoints return `403` for driver sessions.

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `POST` | `/login` | — | Authenticate; sets session cookie |
| `GET` | `/api/drivers/live` | Manager | Full fleet snapshot with KPIs |
| `GET` | `/api/drivers` | Manager | Driver list (for dropdown refresh) |
| `POST` | `/api/assign` | Manager | Dispatch a delivery |
| `POST` | `/api/cancel_delivery` | Manager | Cancel an active delivery |
| `POST` | `/api/register_driver` | Manager | Create a new driver account |
| `GET` | `/api/history` | Manager | Last 100 deliveries; filterable by `?driver=&status=` |
| `GET` | `/api/my_status` | Driver | Own position, ETA, and delivery details |
| `GET` | `/api/driver/history` | Driver | Own last 20 deliveries + lifetime stats |

---

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| 👔 Manager | `manager` | `manager` |
| 🚚 Driver | `driver` | `driver` |

Passwords are stored as **scrypt hashes** — existing plaintext passwords in older databases are migrated automatically on first boot.

The manager can register additional drivers via the **Register** tab. No database tools or restarts required.

> **Production reminder:** Set a strong `SECRET_KEY` environment variable before deploying publicly.

---

## 📁 Project Structure

```
delivery-fleet-tracker/
│
├── 📂 templates/                 # HTML templates
│   ├── driver.html
│   ├── login.html
│   └── manager.html
├── 📄 Dockerfile                 # Container definition (port 7860)
├── 📄 app.py                     # Application entry point
└── 📄 requirements.txt           # Python dependencies
```

---

## 👨‍💻 Author

<div align="center">

<table>
<tr>
<td align="center" width="100%">

<img src="https://avatars.githubusercontent.com/mnoorchenar" width="120" style="border-radius:50%; border: 3px solid #4f46e5;" alt="Mohammad Noorchenarboo"/>

<h3>Mohammad Noorchenarboo</h3>

<code>Data Scientist</code> &nbsp;|&nbsp; <code>AI Researcher</code> &nbsp;|&nbsp; <code>Biostatistician</code>

📍 &nbsp;Ontario, Canada &nbsp;&nbsp; 📧 &nbsp;[mohammadnoorchenarboo@gmail.com](mailto:mohammadnoorchenarboo@gmail.com)

──────────────────────────────────────

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mnoorchenar)&nbsp;
[![Personal Site](https://img.shields.io/badge/Website-mnoorchenar.github.io-4f46e5?style=for-the-badge&logo=githubpages&logoColor=white)](https://mnoorchenar.github.io/)&nbsp;
[![HuggingFace](https://img.shields.io/badge/HuggingFace-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/mnoorchenar)&nbsp;
[![Google Scholar](https://img.shields.io/badge/Scholar-4285F4?style=for-the-badge&logo=googlescholar&logoColor=white)](https://scholar.google.ca/citations?user=nn_Toq0AAAAJ&hl=en)&nbsp;
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mnoorchenar)

</td>
</tr>
</table>

</div>

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

---

## ⚠️ Disclaimer

> [!WARNING]
> This project is developed strictly for educational and research purposes and does not constitute professional advice of any kind. All data is either synthetically generated or publicly available — no real user data is stored or transmitted. This software is provided "as is" without warranty of any kind; use at your own risk.

---

## 📜 License

Distributed under the **MIT License**.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:f59e0b,100:3b82f6&height=120&section=footer&text=Made%20with%20%E2%9D%A4%EF%B8%8F%20by%20Mohammad%20Noorchenarboo&fontColor=ffffff&fontSize=18&fontAlignY=80" width="100%"/>

[![Star on GitHub](https://img.shields.io/badge/%E2%AD%90_Star-on_GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mnoorchenar/delivery-fleet-tracker/stargazers)
[![Fork on GitHub](https://img.shields.io/badge/%F0%9F%8D%B4_Fork-on_GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mnoorchenar/delivery-fleet-tracker/fork)

<sub>The name "DeliveryOS — Fleet Tracking System" is used purely for academic and research purposes. Any similarity to existing product names or trademarks is entirely coincidental. This project has no affiliation with any commercial entity.</sub>

</div>
