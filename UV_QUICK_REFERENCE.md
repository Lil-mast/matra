# UV Package Manager Quick Reference

`uv` is a modern, fast Python package manager written in Rust. It replaces `pip` with better dependency resolution and performance.

## Installation

### Windows (PowerShell)
```powershell
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Verify Installation
```bash
uv --version  # Should show version like: uv 0.1.x
```

---

## Essential Commands for Matra Project

### 1. **Sync Dependencies** (One-time setup)
```bash
# From project root
uv sync

# Creates:
# - .venv/ (virtual environment)
# - uv.lock (lock file for reproducible installs)
```

### 2. **Run Python Commands**
```bash
# Using uv run (automatically activates venv)
uv run python --version
uv run flask --app backend.app run --debug
uv run streamlit run backend/admin_dashboard.py

# Instead of manually activating + python command
```

### 3. **Add New Dependencies**
```bash
# Add a package (updates pyproject.toml & uv.lock)
uv add requests

# Add dev dependency
uv add --dev black

# Add specific version
uv add flask==3.1.1
```

### 4. **Remove Dependencies**
```bash
uv remove requests
uv remove --dev black
```

### 5. **Update Dependencies**
```bash
# Update all packages to latest
uv sync --upgrade

# Update specific package
uv add --upgrade flask
```

### 6. **Install from requirements.txt**
```bash
# Convert requirements.txt to pyproject.toml + uv.lock
uv pip compile backend/requirements.txt -o requirements.lock

# Or directly sync:
uv sync  # Uses pyproject.toml by default
```

### 7. **Export Lock File**
```bash
# Create requirements.lock for reproducible deploys
uv export > requirements.lock

# Use in production
uv pip sync requirements.lock
```

---

## Workflow for Matra Development

### First Time Setup
```bash
cd c:\Users\admin\desktop\matra
uv sync  # Install all dependencies
```

### Daily Development
```bash
# Terminal 1: API Server
uv run flask --app backend.app run --debug

# Terminal 2: Streamlit Dashboard
uv run streamlit run backend/admin_dashboard.py

# Terminal 3: Run tests
uv run pytest backend/tests/ -v
```

### Adding a New Package
```bash
# Need pandas? Add it:
uv add pandas

# Or with exact version:
uv add 'pandas==2.2.3'

# Then commit uv.lock to git for reproducibility
git add uv.lock pyproject.toml
git commit -m "Add pandas dependency"
```

### Before Deployment
```bash
# Ensure lock file is up-to-date
uv sync --upgrade

# Export final lock file
uv export > requirements.lock

# Deploy requirements.lock (more reproducible than requirements.txt)
```

---

## Advanced: Virtual Environment Management

### Use Specific Python Version
```bash
# Install Python 3.11 if needed
uv python install 3.11

# Use Python 3.11 for this project
uv venv -p 3.11 .venv
```

### Manually Activate Virtual Environment (if needed)
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# But with uv, you usually don't need this!
# Just use: uv run <command>
```

### Delete Virtual Environment
```bash
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows
uv sync  # Recreate it
```

---

## Troubleshooting

### Issue: `uv command not found`
```bash
# Add to PATH (Windows)
$env:PATH += ";$env:APPDATA\Python\Scripts"

# Or reinstall
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

### Issue: `No module named 'flask'`
```bash
# Make sure you've run:
uv sync

# Or run commands via uv:
uv run python -c "import flask; print(flask.__version__)"
```

### Issue: Different Python versions between machines
```bash
# Solution: Commit uv.lock to git
# This ensures everyone uses exact same dependency versions

git add uv.lock
git commit -m "Lock dependencies for reproducibility"
```

---

## UV vs PIP Comparison

| Task | pip | uv |
|------|-----|-----|
| Install dependencies | `pip install -r requirements.txt` | `uv sync` |
| Add package | `pip install flask` | `uv add flask` |
| Remove package | Manual edit + `pip uninstall` | `uv remove flask` |
| Create venv | `python -m venv venv` | Automatic with `uv sync` |
| Lock file | Manual with `pip freeze` | Automatic `uv.lock` |
| Speed | ~30-60s | ~1-5s |

**Key Advantage**: `uv` maintains both `pyproject.toml` (human-readable) and `uv.lock` (machine-readable) automatically.

---

## For Production Deployments

### Docker Example
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install uv
RUN pip install uv

# Install dependencies from lock file (more reproducible)
RUN uv export > requirements.lock && pip install -r requirements.lock

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:create_app()"]
```

### Cloud Platform Example (Google Cloud)
```bash
# In app.yaml or similar:
runtime: python311

# Install uv, then sync
install:
  - pip install uv
  - uv sync --no-venv

# Use uv to run app
entrypoint: uv run gunicorn backend.app:create_app()
```

---

## Additional Resources

- **UV Docs**: https://docs.astral.sh/uv/
- **PEP 621** (pyproject.toml standard): https://peps.python.org/pep-0621/
- **PEP 440** (Version specifiers): https://peps.python.org/pep-0440/

