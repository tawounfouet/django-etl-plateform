# Guide d'Installation et Configuration - Plateforme### 2. Création de l'environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel (Linux/Mac)
source .venv/bin/activate

# Activer l'environnement virtuel (Windows)
# .venv\Scripts\activate
```
## Table des Matières

1. [Prérequis](#prérequis)
2. [Installation de l'environnement](#installation-de-lenvironnement)
3. [Création du projet Django](#création-du-projet-django)
4. [Structure du projet](#structure-du-projet)
5. [Configuration des requirements](#configuration-des-requirements)
6. [Configuration Django](#configuration-django)
7. [Configuration des fichiers statiques](#configuration-des-fichiers-s
```bash
# Activer l'environnement virtu```bash
# Installer les dépendances de staging
pip install -r requirements/staging.txt

# Lancer le serveur en mode staging
cd /workspaces/django-etl-plateform
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py runserver 0.0.0.0:8000

# Migrations en staging
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py migrate

# Collecter les fichiers statiques (important pour staging/production)
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py collectstatic --noinput

# Vérifier la configuration
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py check --deploy
```de développement
cd /workspaces/django-etl-plateform
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py runserver

# Ou plus simple (dev par défaut dans manage.py)
python manage.py runserver

# Migrations en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py makemigrations
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py migrate

# Shell Django en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py shell

# Tests en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py test
```ion de l'application principale](#création-de-lapplication-principale)
9. [Tests et validation](#tests-et-validation)
10. [Gestion des Environnements](#gestion-des-environnements)

---
```

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.9+** (recommandé : Python 3.11)
- **pip** (gestionnaire de paquets Python)
- **Git** (pour le contrôle de version)
- **PostgreSQL** (pour la base de données en production)
- **Redis** (pour le cache et les tâches asynchrones)

### Vérification des prérequis

```bash
# Vérifier la version de Python
python --version

# Vérifier pip
pip --version

# Vérifier Git
git --version
```

---

## Installation de l'environnement

### 1. Création du répertoire de travail

```bash
# Créer le répertoire principal
mkdir django-etl-plateform
cd django-etl-plateform
```

### 2. Création de l'environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel (Linux/Mac)
source .venvbin/activate

# Activer l'environnement virtuel (Windows)
# venv\Scripts\activate
```

### 3. Mise à jour de pip

```bash
# Mettre à jour pip vers la dernière version
pip install --upgrade pip
```

---

## Création du projet Django

### 1. Installation de Django

```bash
# Installer Django
pip install Django>=5.2.0
```

### 2. Création du projet

```bash
# Créer le projet Django
django-admin startproject etl_platform .

# Vérifier la structure créée
ls -la
```

### 3. Test initial

```bash
# Tester le serveur de développement
python manage.py runserver

# Le serveur devrait être accessible sur http://127.0.0.1:8000/
```

---

## Structure du projet

### Structure finale organisée

```
django-etl-plateform/
├── etl_platform/           # Configuration principale Django
│   ├── __init__.py
│   ├── settings/           # Settings modulaires
│   │   ├── __init__.py
│   │   ├── base.py        # Configuration de base
│   │   ├── dev.py         # Configuration développement
│   │   ├── staging.py     # Configuration staging
│   │   └── production.py  # Configuration production
│   ├── urls.py            # URLs principales
│   ├── wsgi.py           # WSGI pour déploiement
│   └── asgi.py           # ASGI pour WebSockets
├── apps/                  # Applications Django
│   ├── __init__.py
│   ├── core/             # Application principale
│   ├── etl/              # Fonctionnalités ETL
│   ├── api/              # APIs REST
│   └── authentication/   # Gestion utilisateurs
├── static/               # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── images/
├── staticfiles/          # Fichiers statiques collectés
├── media/                # Fichiers uploadés
├── templates/            # Templates HTML
│   ├── base.html
│   └── core/
├── requirements/         # Dépendances par environnement
│   ├── base.txt         # Dépendances communes
│   ├── dev.txt          # Développement
│   ├── staging.txt      # Staging
│   └── production.txt   # Production
├── docs/                 # Documentation
├── tests/               # Tests
├── logs/                # Fichiers de logs
├── manage.py           # Script de gestion Django
├── .env.example        # Exemple de variables d'environnement
├── .gitignore          # Fichiers à ignorer par Git
└── README.md           # Documentation principale
```

### Commandes pour créer la structure

```bash
# Créer les répertoires principaux
mkdir -p apps/core apps/etl apps/api apps/authentication
mkdir -p static/css static/js static/images
mkdir -p staticfiles media templates/core
mkdir -p requirements docs tests logs

# Créer les fichiers __init__.py pour les packages Python
touch apps/__init__.py
touch apps/core/__init__.py
touch apps/etl/__init__.py
touch apps/api/__init__.py
touch apps/authentication/__init__.py

# Créer la structure des settings
mkdir -p etl_platform/settings
touch etl_platform/settings/__init__.py
```

---

## Configuration des requirements

### 1. Structure des requirements

Nous avons organisé les dépendances par environnement :

#### `requirements/base.txt` - Dépendances communes

```bash
cat > requirements/base.txt << 'EOF'
# Base requirements - shared across all environments
Django>=5.2.0,<5.3.0
djangorestframework>=3.15.0
django-cors-headers>=4.3.0
django-filter>=23.0.0
djangorestframework-simplejwt>=5.3.0

# Database
psycopg2-binary>=2.9.0

# Cache and Message Broker
redis>=5.0.0
django-redis>=5.4.0

# Async Tasks
celery>=5.3.0
kombu>=5.3.0

# Environment and Configuration
python-dotenv>=1.0.0

# Date and Time
python-dateutil>=2.8.0
pytz>=2023.3

# HTTP and API
requests>=2.31.0
urllib3>=2.0.0

# Data Processing
pandas>=2.1.0
numpy>=1.24.0

# Encryption and Security
cryptography>=41.0.0
bcrypt>=4.0.0

# Monitoring and Logging
structlog>=23.0.0
python-json-logger>=2.0.0

# File Processing
openpyxl>=3.1.0
python-magic>=0.4.0

# Validation
marshmallow>=3.20.0
jsonschema>=4.19.0

whitenoise>=6.5.0
EOF
```

#### `requirements/dev.txt` - Développement

```bash
cat > requirements/dev.txt << 'EOF'
-r base.txt

# Development and debugging
django-debug-toolbar>=4.2.0
django-extensions>=3.2.0

# Testing
pytest>=7.4.0
pytest-django>=4.5.0
pytest-cov>=4.1.0
factory-boy>=3.3.0

# Code quality
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.5.0

# Documentation
Sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0
EOF
```

#### `requirements/staging.txt` - Staging

```bash
cat > requirements/staging.txt << 'EOF'
-r base.txt

# Static files serving
whitenoise>=6.5.0

# Basic monitoring for staging
django-debug-toolbar>=4.2.0

# Error tracking
sentry-sdk>=1.32.0
EOF
```

#### `requirements/production.txt` - Production

```bash
cat > requirements/production.txt << 'EOF'
-r base.txt

# Static files serving
whitenoise>=6.5.0

# Production server
gunicorn>=21.0.0

# Monitoring and error tracking
sentry-sdk>=1.32.0
django-health-check>=3.17.0

# Performance
django-cachalot>=2.6.0
EOF
```

### 2. Installation des dépendances

```bash
# Pour le développement
pip install -r requirements/dev.txt

# Pour la production
pip install -r requirements/production.txt
```

---

## Configuration Django

### 1. Configuration modulaire des settings

#### `etl_platform/settings/base.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'rest_framework_simplejwt',
]

LOCAL_APPS = [
    'apps.core',
    'apps.etl',
    'apps.api',
    'apps.authentication',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'etl_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'etl_platform.wsgi.application'
ASGI_APPLICATION = 'etl_platform.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'etl_platform'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

### 2. Configuration par environnement

#### Développement - `etl_platform/settings/dev.py`

```python
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Utiliser SQLite pour le développement (optionnel)
if os.getenv('USE_SQLITE', 'False').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Django Debug Toolbar
if 'django_debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

#### Production - `etl_platform/settings/production.py`

```python
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 3. Mise à jour de manage.py

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Utiliser les settings de développement par défaut
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etl_platform.settings.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

---

## Configuration des fichiers statiques

### 1. WhiteNoise pour la production

WhiteNoise est déjà configuré dans le middleware et les settings de production pour servir les fichiers statiques efficacement.

### 2. Collecte des fichiers statiques

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

---

## Création de l'application principale

### 1. Création de l'app core

```bash
# Créer l'application core
python manage.py startapp core apps/core
```

### 2. Configuration des URLs

#### `etl_platform/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('api/', include('apps.api.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

#### `apps/core/urls.py`

```python
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
]
```

### 3. Vue d'accueil

#### `apps/core/views.py`

```python
from django.shortcuts import render
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Plateforme ETL Django',
            'description': 'Bienvenue sur votre plateforme ETL personnalisée',
        })
        return context
```

---

## Tests et validation

### 1. Migrations

```bash
# Créer et appliquer les migrations
python manage.py makemigrations
python manage.py migrate
```

### 2. Créer un superutilisateur

```bash
# Créer un utilisateur administrateur
python manage.py createsuperuser
```

### 3. Test du serveur

```bash
# Démarrer le serveur de développement
python manage.py runserver 0.0.0.0:8000
```

### 4. Vérifications

- [ ] Page d'accueil accessible on http://localhost:8000
- [ ] Interface admin accessible on http://localhost:8000/admin
- [ ] Fichiers statiques correctement servis
- [ ] Aucune erreur dans les logs

---

## Gestion des Environnements

### Vue d'ensemble des environnements

Notre projet utilise une configuration modulaire avec 4 environnements distincts :

- **`base.py`** : Configuration commune à tous les environnements
- **`dev.py`** : Développement (DEBUG=True, SQLite optionnel, outils de debug)
- **`stg.py`** : Staging/Pré-production (tests avant mise en production)
- **`prod.py`** : Production (sécurité maximale, optimisations)

### Variables d'environnement Django

Pour spécifier l'environnement, utilisez la variable `DJANGO_SETTINGS_MODULE` :

```bash
# Développement (par défaut dans manage.py)
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev

# Staging
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg

# Production
DJANGO_SETTINGS_MODULE=etl_platform.settings.prod
```

### Commandes par environnement

#### Environnement de Développement

```bash
# Activer l'environnement virtuel et lancer en mode développement
cd /workspaces/django-etl-plateform
source .venvbin/activate
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py runserver

# Ou plus simple (dev par défaut dans manage.py)
python manage.py runserver

# Migrations en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py makemigrations
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py migrate

# Shell Django en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py shell

# Tests en développement
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py test
```

#### Environnement de Staging

```bash
# Installer les dépendances de staging
pip install -r requirements/staging.txt

# Lancer le serveur en mode staging
cd /workspaces/django-etl-plateform
source .venvbin/activate
DJANGO_SETTINGS_MODULE=etl_platform.settings.staging python manage.py runserver 0.0.0.0:8000

# Migrations en staging
DJANGO_SETTINGS_MODULE=etl_platform.settings.staging python manage.py migrate

# Collecter les fichiers statiques (important pour staging/production)
DJANGO_SETTINGS_MODULE=etl_platform.settings.staging python manage.py collectstatic --noinput

# Vérifier la configuration
DJANGO_SETTINGS_MODULE=etl_platform.settings.staging python manage.py check --deploy
```

#### Environnement de Production

```bash
# Installer les dépendances de production
pip install -r requirements/production.txt

# Variables d'environnement de production (dans .env ou système)
export DJANGO_SETTINGS_MODULE=etl_platform.settings.prod
export SECRET_KEY="votre-clé-secrète-très-longue-et-complexe"
export DEBUG=False
export ALLOWED_HOSTS="votre-domaine.com,www.votre-domaine.com"

# Migrations en production
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Lancer avec Gunicorn (serveur de production)
gunicorn etl_platform.wsgi:application --bind 0.0.0.0:8000

# Vérifications de sécurité
python manage.py check --deploy
```

### Scripts pratiques

#### Créer des scripts shell pour simplifier

**`scripts/run_dev.sh`**
```bash
#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.dev
python manage.py runserver 0.0.0.0:8000
```

**`scripts/run_stg.sh`**
```bash
#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.stg
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**`scripts/deploy_prod.sh`**
```bash
#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.prod

# Vérifications pré-déploiement
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput

# Lancer avec Gunicorn
gunicorn etl_platform.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Rendre les scripts exécutables

```bash
# Créer le dossier scripts
mkdir -p scripts

# Créer les scripts (copier le contenu ci-dessus)
# Puis les rendre exécutables
chmod +x scripts/run_dev.sh
chmod +x scripts/run_stg.sh
chmod +x scripts/deploy_prod.sh
```

### Configuration avec docker-compose (optionnel)

**`docker-compose.dev.yml`**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE=etl_platform.settings.dev
    command: python manage.py runserver 0.0.0.0:8000
```

**`docker-compose.staging.yml`**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=etl_platform.settings.staging
    command: gunicorn etl_platform.wsgi:application --bind 0.0.0.0:8000
```

### Variables d'environnement par configuration

#### `.env.dev` (Développement)
```bash
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev
SECRET_KEY=dev-secret-key-not-for-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
USE_SQLITE=True
```

#### `.env.stg` (Staging)
```bash
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg
SECRET_KEY=staging-secret-key-different-from-prod
DEBUG=False
ALLOWED_HOSTS=staging.votre-domaine.com
DB_NAME=etl_platform_staging
```

#### `.env.prod` (Production)
```bash
DJANGO_SETTINGS_MODULE=etl_platform.settings.prod
SECRET_KEY=production-secret-key-très-long-et-complexe
DEBUG=False
ALLOWED_HOSTS=www.votre-domaine.com,votre-domaine.com
DB_NAME=etl_platform_production
```

### Commandes de débogage par environnement

```bash
# Vérifier quelle configuration est utilisée
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etl_platform.settings.dev')
django.setup()
from django.conf import settings
print(f'Settings module: {settings.SETTINGS_MODULE}')
print(f'DEBUG: {settings.DEBUG}')
print(f'DATABASES: {settings.DATABASES}')
"

# Lister toutes les migrations
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py showmigrations

# Vérifier les URLs
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py show_urls

# Tester la connexion à la base de données
DJANGO_SETTINGS_MODULE=etl_platform.settings.dev python manage.py dbshell
```

### Bonnes pratiques

1. **Développement** : Utilisez toujours `etl_platform.settings.dev`
2. **Tests locaux staging** : Testez avec `etl_platform.settings.staging` avant déploiement
3. **Production** : Ne jamais utiliser DEBUG=True, toujours collecter les statiques
4. **Variables sensibles** : Utilisez des fichiers `.env` différents par environnement
5. **Scripts** : Créez des scripts shell pour automatiser les tâches répétitives

### Workflow de développement recommandé

```bash
# 1. Développement quotidien
source .venvbin/activate
python manage.py runserver  # (dev par défaut)

# 2. Test avant commit
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py test
DJANGO_SETTINGS_MODULE=etl_platform.settings.stg python manage.py check

# 3. Test staging avant déploiement
./scripts/run_stg.sh

# 4. Déploiement production
./scripts/deploy_prod.sh
```

---

## Ressources

- [Documentation Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)
- [Celery Documentation](https://docs.celeryproject.org/)

---

*Guide créé le 16 juin 2025 - Plateforme ETL Django*
