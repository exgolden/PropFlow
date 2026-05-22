# PropFlow

Property management system for commercial spaces — units, tenants, contracts, invoices, maintenance and documents in one place.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-499848?style=flat&logo=gunicorn&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat&logo=bootstrap&logoColor=white)

## What it does

PropFlow manages the full lifecycle of commercial property rentals:

- **Units** — track offices, locals, warehouses, apartments and more with auto-generated IDs
- **Tenants** — manage company contacts with RFC and email validation
- **Contracts** — link units to tenants with automatic invoice generation on billing day
- **Invoices** — auto-generated monthly by a background scheduler, payment registration included
- **Maintenance** — track requests with priority levels, cumulative journal and cost tracking
- **Documents** — upload and manage files with expiry alerts and signed download links for tenants
- **Users** — role-based access control (root, admin, staff)

## Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.1 + Python 3.14 |
| Database | SQLite with WAL mode |
| Server | Gunicorn behind Nginx |
| Frontend | Bootstrap 5 + vanilla JS |
| Auth | Session-based with bcrypt |
| Scheduler | APScheduler |
| Observability | Structured logs → Loki via Promtail |
| Containerization | Docker + Docker Compose |
