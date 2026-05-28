# Quick Start Guide

Get Matra running in 5 minutes.

## Prerequisites

- Python 3.9+ installed
- Windows/macOS/Linux

---

## 1. Install UV Package Manager

### Windows (PowerShell)
```powershell
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
uv --version
```

---

## 2. Clone & Setup Project

```bash
# Navigate to project
cd c:\Users\admin\desktop\matra

# Install all dependencies (creates .venv automatically)
uv sync

# Verify Flask can import
uv run python -c "from backend.app import create_app; print('✓ Ready!')"
```

---

## 3. Start the Application

### Terminal 1: Flask API
```bash
uv run flask --app backend.app run --debug
```
👉 API available at: **http://localhost:5000**

Test it:
```bash
curl http://localhost:5000/api/health
# Response: {"status": "ok", "service": "matra-api"}
```

### Terminal 2: Streamlit Dashboard
```bash
uv run streamlit run backend/admin_dashboard.py
```
👉 Dashboard available at: **http://localhost:8501**

---

## 4. First Assessment

Create a test user (Terminal 3):
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "test123",
    "role": "hospital",
    "clinic_name": "Test Clinic"
  }'
```

Run a risk assessment:
```bash
curl -X POST http://localhost:5000/api/assess \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "parity": 2,
    "systolic_bp": 165,
    "diastolic_bp": 105,
    "pulse": 95,
    "bleeding": 0,
    "fever": false,
    "convulsions": true,
    "reduced_fetal_movement": false,
    "anemia": false
  }'
```

Response:
```json
{
  "risk_level": "high",
  "recommended_action": "Immediate hospital referral",
  "ml_probability": 0.92
}
```

Login to dashboard:
- **Username**: `admin`
- **Password**: `test123`
- View metrics, referrals, user activity

---

## 5. Run Tests

```bash
uv run pytest backend/tests/ -v
```

---

## Next: Advanced Setup

- 📖 Read **BACKEND_SETUP.md** for detailed configuration
- 📦 Read **UV_QUICK_REFERENCE.md** for package management
- 🧠 See **backend/model/triage_model.py** for risk logic
- 📊 Explore **backend/admin_dashboard.py** for dashboard features

---

## Common UV Commands

```bash
# Add new package
uv add requests

# Update dependencies
uv sync --upgrade

# Run any Python command
uv run python script.py
uv run pytest
uv run black backend/

# Export lock file (for production)
uv export > requirements.lock
```

---

## Troubleshooting

**Flask won't start?**
```bash
# Ensure venv is set up
uv sync

# Try explicit Python path
uv run python -m flask --app backend.app run
```

**Streamlit can't connect to Flask?**
- Ensure Flask terminal is still running
- Flask runs on port 5000, Streamlit on 8501

**Import errors?**
```bash
# Reinstall clean
rm -rf .venv uv.lock
uv sync
```

---

✅ **You're ready to develop!**

Need help? Check BACKEND_SETUP.md or UV_QUICK_REFERENCE.md
