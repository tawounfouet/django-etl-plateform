"""
Development settings for etl_platform project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Database for development (SQLite for simplicity)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Disable HTTPS redirects in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery eager mode for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Debug toolbar
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Logging level for development
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"

# Development-specific ETL settings
ETL_PLATFORM.update({
    "MAX_CONCURRENT_PIPELINES": 3,
    "PIPELINE_TIMEOUT_SECONDS": 300,  # 5 minutes for dev
    "DATA_CHUNK_SIZE": 100,  # Smaller chunks for dev
})
