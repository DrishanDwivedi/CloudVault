# CloudVault

Multi-tier cloud storage platform with automated lifecycle-based file migration across Hot, Warm, and Archive storage tiers.

## Architecture

| Tier    | Backend       | Purpose                    |
|---------|---------------|----------------------------|
| Hot     | MinIO         | Frequently accessed files  |
| Warm    | SeaweedFS     | Infrequently accessed      |
| Archive | Scality S3 Server | Long-term cold storage     |

```
Frontend (React + Vite) ──► Backend (FastAPI) ──► Storage Adapters
                                │
                          ┌─────┴─────┐
                     PostgreSQL    Redis (Celery)
                     (SQLite dev)   (eager mode dev)
```

## Quick Start (Windows)

### Prerequisites

- Python 3.10+
- Node.js 18+
- PowerShell 7+

### Setup

```bat
:: 1. Download storage binaries (MinIO, SeaweedFS)
setup_services.bat

:: 2. Install Python dependencies
venv\Scripts\pip install -r backend\requirements.txt

:: 3. Install frontend dependencies
cd frontend && npm install && cd ..
```

### Run

```bat
:: Launch everything (storage + backend + frontend)
start.bat
```

Or run individually:

```bat
:: Backend only (with mock storage)
set MOCK_STORAGE=True
cd backend && ..\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

:: Frontend only
cd frontend && npm run dev
```

### URLs

| Service            | URL                          |
|--------------------|------------------------------|
| Frontend           | http://localhost:5173        |
| Backend API        | http://localhost:8000        |
| API Docs           | http://localhost:8000/docs   |
| MinIO Hot (UI)     | http://localhost:9001        |
| SeaweedFS (UI)     | http://localhost:8888        |
| Scality Archive    | http://localhost:18000       |

## Docker Deployment

```bash
docker compose up -d
```

This starts all services: PostgreSQL, Redis, MinIO, SeaweedFS, Scality S3 Server, Backend, Celery workers, and Frontend.

## Project Structure

```
backend/
  app/
    adapters/     # Storage backends (MinIO, SeaweedFS, Scality S3)
    api/v1/       # REST endpoints (auth, files, folders, admin)
    core/         # Config, DB, security, Celery
    crud/         # Database operations
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
    tasks/        # Celery async tasks (migration)
frontend/
  src/
    context/      # Auth context (JWT token management)
    pages/        # Login, Register
    App.jsx       # Main dashboard (file explorer, admin panels)
services/         # Storage binaries and runtime data
storage/          # Storage config
```

## API Overview

| Method | Endpoint                    | Auth   | Description              |
|--------|-----------------------------|--------|--------------------------|
| POST   | /api/v1/auth/register       | -      | Register user            |
| POST   | /api/v1/auth/login          | -      | Login, get JWT           |
| GET    | /api/v1/auth/me             | User   | Current user profile     |
| POST   | /api/v1/files/upload        | User   | Upload file              |
| GET    | /api/v1/files/download/{id} | User   | Download file            |
| DELETE | /api/v1/files/{id}          | User   | Delete file              |
| PATCH  | /api/v1/files/{id}          | User   | Rename file              |
| POST   | /api/v1/folders             | User   | Create folder            |
| GET    | /api/v1/folders/contents    | User   | List files/folders       |
| GET    | /api/v1/admin/analytics     | Admin  | Storage distribution     |
| POST   | /api/v1/admin/lifecycle/trigger | Admin | Run migration sweep   |
| GET    | /api/v1/admin/users         | Admin  | List all users           |
| PATCH  | /api/v1/admin/users/{id}    | Admin  | Update user role/status  |
| GET    | /api/v1/admin/migrations    | Admin  | Migration queue          |
| GET    | /api/v1/admin/activities    | Admin  | All activity logs        |

## Lifecycle Policies

Files automatically migrate between tiers based on age:

- **Hot (MinIO)** — files uploaded here first
- **Warm (SeaweedFS)** — after 30 days (configurable)
- **Archive (Scality S3 Server)** — after 90 days (configurable)

Admins can configure durations and trigger manual sweeps from the dashboard.
