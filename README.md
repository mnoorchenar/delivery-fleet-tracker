---
title: delivery-fleet-tracker
colorFrom: yellow
colorTo: blue
sdk: docker
---

<div align="center">

<h1>🚚 DeliveryOS — Fleet Tracking System</h1>
<img src="https://readme-typing-svg.demolab.com?font=Space+Mono&size=20&duration=3000&pause=1000&color=F59E0B&center=true&vCenter=true&width=700&lines=Real-Time+Delivery+Fleet+Tracking;Live+Driver+Location+%26+ETA+Updates;Manager+Dashboard+%7C+Driver+Portal;Simulated+GPS+Movement+Every+10s" alt="Typing SVG"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-4f46e5?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-3b82f6?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Spaces-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/mnoorchenar/spaces)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)](#)

<br/>

**🚚 DeliveryOS** — A full-stack delivery fleet management system with real-time driver tracking, live ETA calculations, and a manager-only dispatch dashboard. Drivers are assigned packages, their GPS position is simulated along the route (store → destination → store), and the system updates every 10 seconds with live ETAs.

<br/>

---

</div>

## Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Getting Started](#-getting-started)
- [Docker Deployment](#-docker-deployment)
- [Dashboard Modules](#-dashboard-modules)
- [Simulation Logic](#-simulation-logic)
- [Project Structure](#-project-structure)
- [Default Credentials](#-default-credentials)
- [Author](#-author)
- [Contributing](#-contributing)
- [Disclaimer](#disclaimer)
- [License](#-license)

---

## ✨ Features

<table>
  <tr>
    <td>🗺️ <b>Live Fleet Map</b></td>
    <td>Interactive Leaflet.js map showing all driver positions, routes, and destination markers, refreshing every 10 seconds</td>
  </tr>
  <tr>
    <td>⏱️ <b>Real-Time ETA Engine</b></td>
    <td>Haversine distance calculations at 35 km/h city speed — ETAs to destination and back to warehouse update continuously</td>
  </tr>
  <tr>
    <td>📦 <b>Dispatch Control</b></td>
    <td>Manager assigns packages to drivers from a curated destination list or custom coordinates, auto-generating package IDs</td>
  </tr>
  <tr>
    <td>👤 <b>Driver Registration</b></td>
    <td>Manager can register new driver accounts in-app — no database tools required</td>
  </tr>
  <tr>
    <td>🔒 <b>Role-Based Access</b></td>
    <td>Manager sees the full fleet dashboard; drivers see only their own assignment, progress, and ETA</td>
  </tr>
  <tr>
    <td>🐳 <b>Containerized Deployment</b></td>
    <td>Docker-first architecture, Hugging Face Spaces ready on port 7860, zero-config SQLite persistence</td>
  </tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DeliveryOS                              │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │  SQLite DB   │───▶│  Flask API   │───▶│  Templates  │  │
│  │  (users,     │    │  (routes,    │    │  (Jinja2 +  │  │
│  │  drivers,    │    │  simulation  │    │  Leaflet.js)│  │
│  │  deliveries) │    │  engine)     │    │             │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
│                              │                             │
│                   ┌──────────▼──────────┐                  │
│                   │  /api/drivers/live  │ ← polled 10s     │
│                   │  /api/my_status     │                  │
│                   └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/mnoorchenar/delivery-fleet-tracker.git
cd delivery-fleet-tracker

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open your browser at `http://localhost:7860` 🎉

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker
docker build -t delivery-fleet-tracker .
docker run -p 7860:7860 delivery-fleet-tracker

# Or with Docker Compose
docker compose up --build
```

---

## 📊 Dashboard Modules

| Module | Description | Status |
|--------|-------------|--------|
| 🗺️ Live Fleet Map | Interactive map with real-time driver markers and route lines | ✅ Live |
| 📋 Driver Fleet List | Sidebar with all drivers, status badges, and ETA display | ✅ Live |
| 📦 Dispatch Panel | Assign packages to drivers with destination picker | ✅ Live |
| 👤 Driver Registration | In-app driver account creation by manager | ✅ Live |
| 📜 Delivery History | Recent 50 deliveries with status and timestamps | ✅ Live |
| 🚚 Driver Portal | Personal dashboard with progress bar, map, and ETA | ✅ Live |

---

## 🧮 Simulation Logic

The GPS simulation runs server-side with no external services required:

```python
# Core Simulation Model in DeliveryOS
simulation = {
    "speed":         "35 km/h (city average)",
    "update_cycle":  "Every 10 seconds via JS polling",
    "position":      "Linear interpolation along great-circle path",
    "dwell_time":    "30 seconds at destination before return",
    "distance":      "Haversine formula (spherical Earth)",
    "trip_phases":   "en_route → at_destination → returning → completed"
}
```

---

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| 👔 Manager | `manager` | `manager` |
| 🚚 Driver | `driver` | `driver` |

The manager can register additional drivers via the **Register** tab in the dashboard.

---

## 📁 Project Structure

```
delivery-fleet-tracker/
│
├── 📄 app.py                   # Flask application — routes, simulation engine, API
│
├── 📂 templates/
│   ├── 📄 login.html           # Authentication page
│   ├── 📄 manager.html         # Manager fleet dashboard (map + dispatch + history)
│   └── 📄 driver.html          # Driver personal dashboard (map + ETA + progress)
│
├── 📄 requirements.txt         # Python dependencies (Flask, gunicorn)
├── 📄 Dockerfile               # Container definition (port 7860, HF Spaces ready)
└── 📄 README.md                # This file
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
[![HuggingFace](https://img.shields.io/badge/HuggingFace-ffcc00?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/mnoorchenar/spaces)&nbsp;
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

## Disclaimer

<span style="color:red">This project is developed strictly for educational and research purposes and does not constitute professional advice of any kind. All datasets used are either synthetically generated or publicly available — no real user data is stored. This software is provided "as is" without warranty of any kind; use at your own risk.</span>

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:f59e0b,100:3b82f6&height=120&section=footer&text=Made%20with%20%E2%9D%A4%EF%B8%8F%20by%20Mohammad%20Noorchenarboo&fontColor=ffffff&fontSize=18&fontAlignY=80" width="100%"/>

[![GitHub Stars](https://img.shields.io/github/stars/mnoorchenar/delivery-fleet-tracker?style=social)](https://github.com/mnoorchenar/delivery-fleet-tracker)
[![GitHub Forks](https://img.shields.io/github/forks/mnoorchenar/delivery-fleet-tracker?style=social)](https://github.com/mnoorchenar/delivery-fleet-tracker/fork)

<sub>The name "DeliveryOS" is used purely for academic and research purposes. Any similarity to existing company names, products, or trademarks is entirely coincidental and unintentional. This project has no affiliation with any commercial entity.</sub>

</div>