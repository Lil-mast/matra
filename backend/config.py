import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with SECURE DEFAULTS for healthcare data."""
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'matra_dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security (CRITICAL: Never use hardcoded secrets in production)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError(
            "CRITICAL: SECRET_KEY environment variable must be set. "
            "Generate one: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # JWT Configuration
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))
    JWT_ALGORITHM = "HS256"
    
    # CORS (restrict to known domains in production)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    
    # Rate Limiting (CRITICAL for public endpoints)
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200/hour")
    
    # Voice agent configuration
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
    VOICE_STT_MODEL = os.environ.get("VOICE_STT_MODEL", "openai/whisper-small")
    VOICE_STT_DEVICE = os.environ.get("VOICE_STT_DEVICE", "cpu")
    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "Rachel")
    VOICE_SESSION_TIMEOUT_SECONDS = int(os.environ.get("VOICE_SESSION_TIMEOUT_SECONDS", "3600"))

    # Health Data Security (GDPR/HIPAA compliance)
    ENCRYPT_DATABASE = os.environ.get("ENCRYPT_DATABASE", "true").lower() == "true"
    AUDIT_LOG_ENABLED = os.environ.get("AUDIT_LOG_ENABLED", "true").lower() == "true"
    DATA_RETENTION_DAYS = int(os.environ.get("DATA_RETENTION_DAYS", "2555"))  # 7 years default
    
    # Authentication for /api/assess in production
    # If ASSESS_REQUIRES_AUTH=true, clients must provide API key or JWT token
    ASSESS_REQUIRES_AUTH = os.environ.get("ASSESS_REQUIRES_AUTH", "false").lower() == "true"
    
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development config with relaxed security (dev only!)."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    RATELIMIT_DEFAULT = "10000/hour"  # Disable rate limiting in dev
    ASSESS_REQUIRES_AUTH = False  # Allow offline testing
    ENCRYPT_DATABASE = False  # Overhead in dev
    AUDIT_LOG_ENABLED = False  # Less verbose logging in dev


class TestingConfig(Config):
    """Testing config with in-memory database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_DEFAULT = "10000/hour"  # Disable rate limiting in tests
    ASSESS_REQUIRES_AUTH = False
    ENCRYPT_DATABASE = False
    AUDIT_LOG_ENABLED = True  # Track test execution


class ProductionConfig(Config):
    """Production config with maximum security hardening."""
    # CRITICAL: All values must come from environment variables
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required in production")
    
    DEBUG = False
    TESTING = False
    RATELIMIT_DEFAULT = "100/hour"  # Strict rate limiting
    ASSESS_REQUIRES_AUTH = True  # CRITICAL: Require auth in production
    ENCRYPT_DATABASE = True  # CRITICAL: Enable encryption
    AUDIT_LOG_ENABLED = True  # CRITICAL: Enable audit logging
    
