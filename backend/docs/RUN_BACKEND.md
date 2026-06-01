# Running the Backend

This document explains how to run the Matra backend from the `backend/` directory.

## Prerequisites

- Python 3.9 or newer
- `uv` package manager installed (recommended)
- Optional: virtual environment

## Install dependencies

From the project root:

```bash
# Install dependencies using uv
uv sync

# Or install directly with pip
pip install -r backend/requirements.txt
```

If you want to use a local virtual environment manually:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
```

## Set required environment variables

The backend requires a secure `SECRET_KEY`. Create one if you do not already have it:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then set it before running the app.

### Windows PowerShell example

```powershell
$env:SECRET_KEY = "your-generated-secret"
$env:DATABASE_URL = "sqlite:///matra_dev.db"
$env:ASSESS_REQUIRES_AUTH = "false"
$env:RATELIMIT_DEFAULT = "200/hour"
```

DATABASE_URL = "sqlite:///matra_dev.db"
ASSESS_REQUIRES_AUTH = "false"
RATELIMIT_DEFAULT = "200/hour"

### Windows CMD example

```cmd
set SECRET_KEY=your-generated-secret
set DATABASE_URL=sqlite:///matra_dev.db
set ASSESS_REQUIRES_AUTH=false
set RATELIMIT_DEFAULT=200/hour
```

## Run the Flask API server

From the project root or from inside `backend/`:

```bash
uv run flask --app backend.app run --debug
```

This starts the API server on:

- `http://127.0.0.1:5000`

### Production-like run with Gunicorn

```bash
uv run gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

## Verify the backend is running

Use the health endpoint:

```bash
curl http://127.0.0.1:5000/api/health
```

Expected response:

```json
{"status": "ok", "service": "matra-api"}
```

## Admin dashboard

To run the dashboard in a separate terminal:

```bash
uv run streamlit run backend/admin_dashboard.py
```

Then open the browser at:

- `http://localhost:8501`

## Notes

- If you run from inside `backend/`, use `python -m venv .venv` and `uv` from the activated environment or global install.
- In production, set `ASSESS_REQUIRES_AUTH=true` and use a real database URL.
- The backend automatically creates database tables on startup using SQLAlchemy.
