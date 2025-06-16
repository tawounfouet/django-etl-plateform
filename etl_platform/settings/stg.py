"""
Staging settings for etl_platform project.
"""

from .base import *

DEBUG = True  # Enable debug in staging for testing

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "staging.etl-platform.com").split(",")

# Add WhiteNoise middleware for static files serving in staging
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Use PostgreSQL in staging (similar to production)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "etl_platform_staging"),
        "USER": os.getenv("DB_USER", "etl_user"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": 60,
        },
        "CONN_MAX_AGE": 300,
    }
}

# Email backend for staging
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Less strict security for staging
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS settings for staging
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://staging-frontend.etl-platform.com",
]

# Logging for staging
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"

# Staging-specific ETL settings
ETL_PLATFORM.update({
    "MAX_CONCURRENT_PIPELINES": int(os.getenv("MAX_CONCURRENT_PIPELINES", "5")),
    "PIPELINE_TIMEOUT_SECONDS": int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "1800")),  # 30 minutes
    "DATA_CHUNK_SIZE": int(os.getenv("DATA_CHUNK_SIZE", "1000")),
})
