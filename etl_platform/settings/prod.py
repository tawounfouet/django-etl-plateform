"""
Production settings for etl_platform project.
"""

from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Add WhiteNoise middleware for static files serving
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use environment variables for sensitive settings
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")

# Database settings for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",
            "connect_timeout": 60,
            "options": "-c statement_timeout=30000"  # 30 seconds
        },
        "CONN_MAX_AGE": 600,
    }
}

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@etl-platform.com")

# Static files for production with WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Logging for production - structured JSON logs
LOGGING["formatters"]["json"] = {
    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
    "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
}

LOGGING["handlers"]["file"]["formatter"] = "json"
LOGGING["handlers"]["syslog"] = {
    "class": "logging.handlers.SysLogHandler",
    "facility": "local7",
    "formatter": "json",
}

# Add syslog to all loggers in production
for logger_config in LOGGING["loggers"].values():
    if "syslog" not in logger_config["handlers"]:
        logger_config["handlers"].append("syslog")

# CORS settings for production
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True

# Production-specific ETL settings
ETL_PLATFORM.update({
    "MAX_CONCURRENT_PIPELINES": int(os.getenv("MAX_CONCURRENT_PIPELINES", "20")),
    "PIPELINE_TIMEOUT_SECONDS": int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "7200")),  # 2 hours
    "DATA_CHUNK_SIZE": int(os.getenv("DATA_CHUNK_SIZE", "5000")),
    "ENCRYPTION_KEY": os.getenv("ENCRYPTION_KEY"),
})
