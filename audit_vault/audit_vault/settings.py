"""Django settings for audit_vault project.

Generated for the Tamper‑Proof Audit Vault prototype.
Only essential settings are included – adjust DATABASES for production.
"""

import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'replace-this-with-a-secure-key'
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',  # needed for Django internals, but we won't use its User model
    'ledger',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    # Custom token authentication middleware (executes after common middleware)
    'ledger.middleware.TokenAuthMiddleware',
]

ROOT_URLCONF = 'audit_vault.urls'

TEMPLATES = []  # No template rendering needed

WSGI_APPLICATION = 'audit_vault.wsgi.application'

# ---------------------------------------------------------------------------
# Database configuration – switched to PostgreSQL for production.
# Install the driver with: pip install psycopg2-binary
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'audit_vault'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Simple token list for the custom authentication middleware.
# Populate with secure tokens in production (e.g., via environment variable).
API_TOKENS = os.getenv('API_TOKENS', '').split(',') if os.getenv('API_TOKENS') else []

# Internationalisation (defaults)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
