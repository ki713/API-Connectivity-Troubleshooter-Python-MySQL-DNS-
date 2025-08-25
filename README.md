# API Connectivity Troubleshooter (Python + MySQL + DNS)

A diagnostic toolkit that simulates API calls, verifies database state (MySQL), and checks DNS resolution — designed to mimic **Exotel-style incident debugging** (API failures, DNS misconfig, data mismatch).

> Outcome: Faster RCA, reproducible evidence, and clean reports (CSV/JSON) you can share with teams.

---

## Features
- 🔗 **API Checks**: single endpoint or Postman collection runner (no Newman required)
- 🗄️ **DB Checks**: run MySQL queries and validate expected state
- 🌐 **DNS Checks**: A/AAAA/CNAME resolution + latency
- 🧾 **Reports**: consolidated `report.json` and `report.csv` (component, status, latency, details)

---

## Tech Stack
- Python: `requests`, `mysql-connector-python`, `dnspython`, `pandas`
- Linux shell wrapper
- Optional Postman collection support

---

## Setup
```bash
git clone https://github.com/yourusername/api-connectivity-troubleshooter.git
cd api-connectivity-troubleshooter
pip install -r requirements.txt
