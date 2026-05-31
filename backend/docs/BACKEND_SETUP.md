# Backend Setup & Progress Guide

## Overview

**Matra** is a maternal health risk triage system with offline-first architecture. The backend is built with **Flask**, uses a lightweight **scikit-learn logistic regression model** for risk stratification, and integrates a **Streamlit-based admin dashboard** for real-time analytics.

### Technology Stack

- **Framework**: Flask 3.1.1
- **Database**: SQLAlchemy with SQLite (dev) / PostgreSQL (production)
- **Authentication**: JWT + bcrypt
- **Risk Model**: scikit-learn logistic regression + WHO rule-based checks
- **Admin Dashboard**: Streamlit with Plotly analytics
- **Package Manager**: `uv` (recommended)

---

## Getting Started

### Prerequisites

- Python 3.9+
- `uv` package manager (or `pip`)

### Installation with `uv`

`uv` is a fast, drop-in replacement for pip with better dependency resolution. Install it:

```bash
# On Windows (PowerShell)
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Backend Environment

```bash
# Navigate to project root
cd c:\Users\admin\desktop\matra

# Install dependencies using uv (creates virtual env automatically)
uv sync

# Alternatively, if you prefer pip
pip install -r backend/requirements.txt

# Create virtual environment manually (if needed)
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Verify Installation

```bash
# Check uv version
uv --version

# Check Python environment
uv run python --version

# Test Flask app import
uv run python -c "from backend.app import create_app; print('✓ Flask app imports successfully')"
```

---

## Project Structure

```
backend/
├── app.py                 # Flask API factory & core endpoints
├── config.py              # Configuration (Dev/Test/Prod)
├── models.py              # Database models (User, MaternalIntake)
├── requirements.txt       # Dependencies (pip format)
├── admin_dashboard.py     # Streamlit analytics dashboard
│
├── model/
│   ├── __init__.py
│   ├── train.py           # Model training pipeline
│   ├── triage_model.py    # Risk evaluation engine (rule-based + ML)
│   └── model.joblib       # Trained sklearn model (binary)
│
└── tests/
    ├── __init__.py
    ├── test_auth.py       # Authentication tests
    └── test_triage.py     # Risk model tests
```

---

## Running the Application

### 1. Start Flask API Server

```bash
# Development (hot-reload)
uv run flask --app backend.app run --debug

# Production (with Gunicorn)
uv run gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

The API will be available at: `http://localhost:5000`

**Health Check**:
```bash
curl http://localhost:5000/api/health
# Response: {"status": "ok", "service": "matra-api"}
```

### 2. Launch Streamlit Admin Dashboard

In a **new terminal**:

```bash
# Activate same environment
uv run streamlit run backend/admin_dashboard.py

# Or with pip
streamlit run backend/admin_dashboard.py
```

Dashboard will open at: `http://localhost:8501`

**Login Credentials** (for testing):
- Default admin user must be created via `/api/auth/register` endpoint
- Role must be `hospital` or `manager` for dashboard access

---

## API Endpoints

### Authentication

```bash
# Register new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "chw_john",
    "password": "secure_password",
    "role": "chw",
    "clinic_name": "Rural Clinic A"
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "chw_john",
    "password": "secure_password"
  }'
# Response: {"token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "user_id": 1, "role": "chw"}
```

### Risk Assessment

```bash
# Single real-time assessment
# SECURITY: In production, ASSESS_REQUIRES_AUTH=true enforces authentication
# For development/offline use, you can disable auth with ASSESS_REQUIRES_AUTH=false

# With authentication (recommended for production)
curl -X POST http://localhost:5000/api/assess \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "parity": 2,
    "systolic_bp": 165,
    "diastolic_bp": 105,
    "pulse": 95,
    "bleeding": 0,
    "fever": false,
    "convulsions": false,
    "reduced_fetal_movement": false,
    "anemia": false
  }'

# Without authentication (development only)
# Endpoint is still rate-limited even without auth
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
    "convulsions": false,
    "reduced_fetal_movement": false,
    "anemia": false
  }'
```

**CRITICAL SECURITY NOTES**:
- ⚠️ **NEVER expose `/api/assess` publicly without authentication** — it can be abused for DoS attacks
- ✅ **In production**, set `ASSESS_REQUIRES_AUTH=true` to require JWT/API key authentication
- ✅ **Rate limiting is enabled** by default (200 requests/hour) and can be configured
- ✅ **All assessments are logged** for audit trails (if enabled)
```

### Batch Sync (Offline Intakes)

```bash
# Sync batch of offline assessments
curl -X POST http://localhost:5000/api/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '[
    {"age": 30, "parity": 3, "systolic_bp": 150, "diastolic_bp": 95, ...},
    {"age": 25, "parity": 1, "systolic_bp": 130, "diastolic_bp": 85, ...}
  ]'
```

### Metrics & Reporting

```bash
# Get aggregated statistics (requires token)
curl -X GET http://localhost:5000/api/metrics \
  -H "Authorization: Bearer <token>"

# Get referral list (high/intermediate risk)
curl -X GET http://localhost:5000/api/referrals?page=1&per_page=20 \
  -H "Authorization: Bearer <token>"
```

---

## Database

### Initialize Database

```bash
# Create tables automatically on app startup
uv run python -c "
from backend.app import create_app
from backend.config import Config
app = create_app(Config)
with app.app_context():
    from backend.models import db
    db.create_all()
    print('✓ Database initialized')
"
```

### Database Models

**User** (Authentication)
- `id` (PK)
- `username` (unique)
- `password_hash`
- `role` (chw | hospital | manager)
- `clinic_name`
- `created_at`

**MaternalIntake** (Assessments)
- `id` (PK)
- Demographics: `age`, `parity`
- Vitals: `systolic_bp`, `diastolic_bp`, `pulse`
- Danger Signs: `bleeding`, `fever`, `convulsions`, `reduced_fetal_movement`, `anemia`
- Outcome: `risk_level`, `recommended_action`, `ml_probability`
- Metadata: `user_id` (FK), `created_at`, `is_synced`

---

## Risk Triage Model

The triage engine combines two layers:

### 1. Rule-Based Tier (WHO Maternal Danger Signs)

**HIGH RISK triggers**:
- Convulsions/eclampsia
- Severe vaginal bleeding (≥2)
- Severe hypertension (systolic ≥160 OR diastolic ≥110)
- Very high fever (≥39°C)

**INTERMEDIATE triggers**:
- Moderate hypertension (140-159 / 90-109)
- Light bleeding (1)
- Reduced fetal movement
- Severe anemia

### 2. ML Tier (scikit-learn Logistic Regression)

When no absolute danger sign fires, the model refines the classification:
- Input features: age, parity, vitals, danger sign presence
- Output: probability score & intermediate vs. low recommendation

**Model Location**: `backend/model/model.joblib` (trained using scikit-learn)

**Retraining** (see `backend/model/train.py`):
```bash
uv run python backend/model/train.py --data backend/model/training_data.csv
```

---

## Testing

### Run Unit Tests

```bash
# Run all tests with coverage
uv run pytest --cov=backend tests/

# Run specific test file
uv run pytest backend/tests/test_triage.py -v

# Run with verbose output
uv run pytest backend/tests/ -vv --tb=short
```

### Test Coverage Report

```bash
uv run pytest --cov=backend --cov-report=html tests/
# Open: htmlcov/index.html in browser
```

---

## Configuration Management

### Secure Environment Setup (CRITICAL)

The `backend/config.py` file now requires a **SECRET_KEY** environment variable. Never hardcode secrets!

```python
# backend/config.py (excerpt)
class Config:
    """Base configuration with SECURE DEFAULTS for healthcare data."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError(
            "CRITICAL: SECRET_KEY environment variable must be set. "
            "Generate one: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Rate limiting (CRITICAL for public endpoints)
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200/hour")
    
    # Authentication for /api/assess in production
    ASSESS_REQUIRES_AUTH = os.environ.get("ASSESS_REQUIRES_AUTH", "false").lower() == "true"
    
    # Health data encryption (GDPR/HIPAA compliance)
    ENCRYPT_DATABASE = os.environ.get("ENCRYPT_DATABASE", "true").lower() == "true"
    AUDIT_LOG_ENABLED = os.environ.get("AUDIT_LOG_ENABLED", "true").lower() == "true"
```

### Configuration by Environment

#### Development
```bash
# Create .env file in project root
cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
DATABASE_URL=sqlite:///matra_dev.db
ASSESS_REQUIRES_AUTH=false
RATELIMIT_DEFAULT=10000/hour
ENCRYPT_DATABASE=false
EOF

# Load environment
source .env  # macOS/Linux
# or in Windows PowerShell:
Get-Content .env | foreach { $_.split('=') | select -first 1 | foreach { [Environment]::SetEnvironmentVariable($_, (($_ + '=' + $_[$_.length]).split('='))[1]) } }

# Run Flask
uv run flask --app backend.app run --debug
```

#### Production (CRITICAL: Follow these steps exactly)
```bash
# 1. Generate a secure SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'
# Output: xyz123abc456...

# 2. Set environment variables (use your platform's secret manager)
#    AWS: AWS Secrets Manager / Parameter Store
#    GCP: Secret Manager
#    Azure: Key Vault
#    Docker: docker secrets
#    Kubernetes: kubectl secrets

# Example for Linux environment:
export SECRET_KEY="your-generated-secret-key"
export DATABASE_URL="postgresql://user:password@db.example.com/matra_prod"
export FLASK_ENV=production
export ASSESS_REQUIRES_AUTH=true
export ENCRYPT_DATABASE=true
export AUDIT_LOG_ENABLED=true
export RATELIMIT_DEFAULT=100/hour

# 3. Start with Gunicorn
uv run gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app(Config)"

# 4. Use HTTPS/TLS (via nginx or load balancer)
```

### Configuration Classes

```python
# DevelopmentConfig: Relaxed security for local development
DEBUG = True
ASSESS_REQUIRES_AUTH = False
RATELIMIT_DEFAULT = "10000/hour"
ENCRYPT_DATABASE = False

# ProductionConfig: Maximum security hardening
DEBUG = False
ASSESS_REQUIRES_AUTH = True  # CRITICAL
ENCRYPT_DATABASE = True       # CRITICAL
AUDIT_LOG_ENABLED = True      # CRITICAL
RATELIMIT_DEFAULT = "100/hour"
```

### .env File (.gitignore this!)

```bash
# .env (DO NOT COMMIT TO GIT)
SECRET_KEY=your-32-character-secret-key
DATABASE_URL=postgresql://user:pass@localhost/matra_prod
FLASK_ENV=production
ASSESS_REQUIRES_AUTH=true
ENCRYPT_DATABASE=true
AUDIT_LOG_ENABLED=true
RATELIMIT_DEFAULT=100/hour
CORS_ORIGINS=app.example.com,admin.example.com
JWT_EXPIRATION_HOURS=24
REDIS_URL=redis://localhost:6379
```

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

---

## Development Workflow

### 1. Make Code Changes

```bash
# Example: Update risk model logic
nano backend/model/triage_model.py
```

### 2. Run Tests

```bash
uv run pytest backend/tests/test_triage.py -v
```

### 3. Format & Lint

```bash
# Auto-format code
uv run black backend/

# Sort imports
uv run isort backend/

# Check style
uv run flake8 backend/ --max-line-length=100
```

### 4. Test API Locally

```bash
# Terminal 1: Start API
uv run flask --app backend.app run --debug

# Terminal 2: Test endpoint
curl -X POST http://localhost:5000/api/assess -H "Content-Type: application/json" -d '{"age": 28, ...}'
```

---

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r backend/requirements.txt
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:create_app()"]
```
---

## Progress Checklist

### ✅ Completed
- [x] Flask API core endpoints (auth, assess, sync, metrics, referrals)
- [x] SQLAlchemy ORM models (User, MaternalIntake)
- [x] JWT authentication & token-based access control
- [x] Scikit-learn risk model with rule-based WHO checks
- [x] Unit tests for auth and triage logic
- [x] Streamlit admin dashboard with analytics
- [x] Project structure with `pyproject.toml` & `uv` support

### 🚀 Next Steps

#### Phase 1: Offline-First Features (Priority)
- [ ] **LM Studio Integration** for symptom parsing (Mistral 7B)
  - Parse natural language symptom descriptions → structured data
  - Fall back to rule engine if LLM unavailable
  - Cache model locally for offline use

- [ ] **Mobile-Friendly API**
  - Implement GraphQL endpoint (optional, for mobile clients)
  - Add batch assessment request compression
  - Implement data sync queue for unreliable networks

#### Phase 2: Production Hardening (CRITICAL - DO NOT SKIP)

**⚠️ SECURITY & COMPLIANCE REQUIREMENTS (Legal Obligation)**

Healthcare systems must comply with:
- **HIPAA** (Health Insurance Portability and Accountability Act) — US
- **GDPR** (General Data Protection Regulation) — EU
- **Local Health Data Laws** — varies by country
- **HITECH Act** — US security/breach notification

- [ ] **Authentication & Authorization**
  - ✅ DONE: Require authentication on `/api/assess` in production (`ASSESS_REQUIRES_AUTH=true`)
  - ✅ DONE: Rate limiting on all endpoints (200-100 req/hour by environment)
  - ✅ DONE: JWT token validation with expiration
  - [ ] Implement API keys for third-party integrations
  - [ ] Add role-based access control (RBAC) for admin features

- [ ] **Encryption & Data Protection**
  - ✅ DONE: Environment variables for secrets (never hardcode)
  - [ ] Implement database field-level encryption (sqlalchemy-encrypt)
  - [ ] Enable TLS/HTTPS in production (Let's Encrypt + nginx)
  - [ ] Hash sensitive data before storage
  - [ ] Implement secure password reset flows

- [ ] **Data Anonymization & GDPR Compliance**
  - [ ] Remove PII from assessments (no names, national IDs, precise locations)
  - [ ] Implement data export (GDPR "Right to Data Portability")
  - [ ] Implement data deletion (GDPR "Right to Erasure")
  - [ ] Add consent tracking for data processing
  - [ ] Document data processing activities (Data Processing Agreement)

- [ ] **Audit Logging & Accountability**
  - ✅ DONE: Assessment audit trail logging
  - [ ] Log all authentication attempts (success/failure)
  - [ ] Log all data access and modifications
  - [ ] Implement tamper-proof audit logs (immutable)
  - [ ] Alert on suspicious activity patterns

- [ ] **Database Migration & Backups**
  - [ ] Migrate from SQLite to PostgreSQL (production only)
  - [ ] Implement encrypted database backups
  - [ ] Regular backup testing (restore drills)
  - [ ] Backup retention policy (7+ years for healthcare)

- [ ] **Monitoring & Alerting**
  - [ ] Structured logging (ELK stack or Cloud Logging)
  - [ ] Performance monitoring (API response times, model inference)
  - [ ] Security monitoring (failed logins, rate limit breaches)
  - [ ] Error tracking (Sentry)
  - [ ] Health check monitoring

#### Phase 3: Advanced Features
- [ ] **Model Retraining Pipeline**
  - Collect anonymized assessment outcomes
  - Retrain scikit-learn model monthly
  - A/B test new models before deployment

- [ ] **Multi-Language Support**
  - Localize API error messages
  - Support Swahili/French symptom descriptions (LLM-based)

- [ ] **Integration with EHR Systems**
  - FHIR-compliant endpoints for interoperability
  - HL7 message parsing for clinic data imports

#### Phase 4: Scaling & Optimization
- [ ] **Caching Layer**
  - Redis for session management & model cache
  - Reduce database queries for metrics

- [ ] **Distributed Task Queue**
  - Celery + Redis for async model retraining
  - Background batch processing of offline intakes

- [ ] **Load Testing**
  - Test with 10k+ concurrent assessments
  - Optimize database indexes & query plans

---

## ⚖️ LEGAL & COMPLIANCE REQUIREMENTS

### Healthcare Data Protection (Non-Negotiable)

**Matra handles sensitive maternal health data. Deployment requires compliance with:**

| Regulation | Scope | Key Requirements |
|-----------|-------|------------------|
| **HIPAA** (US) | US healthcare | 164-bit encryption, breach notification, audit logs, access controls |
| **GDPR** (EU) | EU citizens | Consent, right to erasure, data portability, breach notification within 72h |
| **PIPEDA** (Canada) | Canadian health data | Consent, security safeguards, personal information access |
| **POPIA** (South Africa) | South African data | Lawful basis, limited collection, security, user rights |
| **Local Laws** | Your country | Check with health ministry/data protection authority |

### Pre-Deployment Checklist

**🔒 Security Controls** (CRITICAL)
- [ ] All data in transit encrypted (HTTPS/TLS 1.3+)
- [ ] All data at rest encrypted (AES-256 for database)
- [ ] Secrets in environment variables, never hardcoded
- [ ] Rate limiting enabled on public endpoints
- [ ] Authentication required for assessment endpoint in production
- [ ] CORS restricted to known domains
- [ ] SQL injection protection (using ORM, parameterized queries)

**📋 Data Protection** (CRITICAL)
- [ ] NO personally identifiable information (names, national IDs, phone numbers) stored
- [ ] NO precise geographic coordinates (only region/district if necessary)
- [ ] Data retention policy documented (e.g., 7 years for healthcare)
- [ ] Data deletion/anonymization process implemented
- [ ] User consent obtained and documented for data processing

**📊 Audit & Accountability** (CRITICAL)
- [ ] All assessments logged with timestamp and user ID
- [ ] Authentication logs (successful/failed attempts)
- [ ] Audit logs immutable and tamper-proof
- [ ] Audit logs retained for 3+ years
- [ ] Regular audit log reviews (monthly)

**🔐 Access Control** (CRITICAL)
- [ ] Users have unique credentials (no shared accounts)
- [ ] Passwords salted and hashed (bcrypt minimum)
- [ ] Roles enforced (CHW, hospital staff, manager)
- [ ] Admin access restricted to authorized personnel
- [ ] Login attempts rate-limited (prevent brute force)
- [ ] Sessions expire after inactivity (24 hours default)

**📝 Documentation** (CRITICAL for legal compliance)
- [ ] Data Processing Agreement (DPA) with stakeholders
- [ ] Privacy Policy available to users
- [ ] Terms of Service for app users
- [ ] Incident response plan documented
- [ ] Data retention schedule documented
- [ ] Risk assessment (DPIA) completed

### Incident Response

If you discover a data breach:

1. **Immediately isolate** the affected system
2. **Notify** data protection authority within 72 hours (GDPR) or as required by law
3. **Document** the incident: what, when, how, scope, and impact
4. **Notify users** affected by the breach
5. **Implement fixes** to prevent recurrence
6. **Retain evidence** for investigation

### Legal Liability

**⚠️ Non-compliance can result in:**
- Regulatory fines: up to €20M or 4% of annual revenue (GDPR)
- Criminal prosecution (HIPAA violations)
- Civil lawsuits from affected individuals
- Operational shutdown orders

**You are legally liable for:**
- Unauthorized access to health data
- Data breaches (even if unintentional)
- Lack of data protection measures
- Inadequate consent/transparency
- Failure to honor user rights (erasure, portability, etc.)

### Recommended Resources

- **HIPAA Compliance Guide**: https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/
- **GDPR Compliance**: https://gdpr-info.eu/
- **WHO Security Guidelines**: https://www.who.int/publications/i/item/9789241515467
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Consult a lawyer** familiar with healthcare regulations in your region

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'flask'`

**Solution**: Ensure virtual environment is activated
```bash
# Activate environment
uv sync
# Or manually:
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: Database locked when running tests

**Solution**: Use separate test database
```bash
# In config.py
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
```

### Issue: Streamlit dashboard loads but can't connect to Flask

**Solution**: Ensure Flask API is running in a separate terminal
```bash
# Terminal 1: Flask API
uv run flask --app backend.app run --debug

# Terminal 2: Streamlit dashboard
uv run streamlit run backend/admin_dashboard.py
```

### Issue: LM Studio model too slow for real-time assess

**Solution**: Pre-cache embeddings or use smaller quantized model
```bash
# Use Phi-2 (2.7B) instead of Llama 2 7B
# Or apply Q4_K_M quantization to reduce memory & improve speed
```

---

## Support & Documentation

- **API Docs**: Postman collection available in `docs/` folder
- **Model Details**: See `backend/model/README.md`
- **Contributing**: See `CONTRIBUTING.md` for development guidelines
- **Issues**: Report bugs at GitHub Issues tracker

---

## License

Matra is released under the **MIT License** for educational and research purposes.  
**Healthcare Use**: For clinical deployment, ensure compliance with local health data protection regulations (HIPAA, GDPR, etc.).

