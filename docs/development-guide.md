# Guide de Développement - Django ETL Platform

## Prérequis

### Outils requis
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Node.js 18+ (pour le frontend)
- Git

### Setup de l'environnement de développement

#### 1. Installation locale

```bash
# Cloner le repository
git clone https://github.com/your-org/django-etl-platform.git
cd django-etl-platform

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements/dev.txt

# Installer pre-commit hooks
pre-commit install

# Variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations locales
```

#### 2. Configuration base de données

```bash
# Démarrer PostgreSQL et Redis avec Docker
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Migrations
python manage.py migrate

# Créer superuser
python manage.py createsuperuser

# Charger données de test
python manage.py loaddata fixtures/dev_data.json
```

#### 3. Démarrage des services

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A etl_platform worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A etl_platform beat --loglevel=info

# Terminal 4: Frontend (si applicable)
cd frontend
npm install
npm run dev
```

## Structure du projet

```
django-etl-platform/
├── etl_platform/              # Projet Django principal
│   ├── settings/              # Settings par environnement
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── staging.py
│   │   └── production.py
│   ├── celery_app.py          # Configuration Celery
│   └── urls.py
├── apps/                      # Applications Django
│   ├── core/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   └── middleware.py
│   ├── connectors/
│   │   ├── models.py
│   │   ├── base.py            # BaseConnector
│   │   ├── database/          # Connecteurs DB
│   │   ├── api/               # Connecteurs API
│   │   ├── file/              # Connecteurs fichiers
│   │   └── tests/
│   ├── pipelines/
│   │   ├── models.py
│   │   ├── builder.py         # Pipeline builder
│   │   ├── dag.py             # DAG generator
│   │   └── validators.py
│   ├── tasks/
│   │   ├── base.py            # BaseTask
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   └── utils.py
│   ├── execution/
│   │   ├── scheduler.py
│   │   ├── engine.py
│   │   └── monitors.py
│   ├── monitoring/
│   │   ├── metrics.py
│   │   ├── alerts.py
│   │   └── dashboard.py
│   └── ui/
│       ├── api/               # API endpoints
│       ├── templates/
│       └── static/
├── requirements/              # Dependencies par environnement
│   ├── base.txt
│   ├── dev.txt
│   ├── staging.txt
│   └── production.txt
├── tests/                     # Tests intégration
├── docs/                      # Documentation
├── scripts/                   # Scripts utilitaires
├── frontend/                  # Application React/Vue
├── docker/                    # Dockerfiles
├── k8s/                       # Manifests Kubernetes
└── migrations/                # Migrations SQL custom
```

## Standards de développement

### Code Style

#### Python
```python
# Configuration dans pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### Conventions de nommage
```python
# Classes: PascalCase
class PipelineExecutor:
    pass

# Fonctions/méthodes: snake_case
def execute_pipeline():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private methods: _snake_case
def _validate_config():
    pass
```

### Architecture patterns

#### 1. Repository Pattern pour data access
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class PipelineRepository(ABC):
    @abstractmethod
    def get_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        pass
    
    @abstractmethod
    def get_active_pipelines(self) -> List[Pipeline]:
        pass

class DjangoPipelineRepository(PipelineRepository):
    def get_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        try:
            return Pipeline.objects.get(id=pipeline_id)
        except Pipeline.DoesNotExist:
            return None
```

#### 2. Service Layer Pattern
```python
class PipelineService:
    def __init__(self, repository: PipelineRepository):
        self.repository = repository
        self.executor = PipelineExecutor()
    
    def execute_pipeline(self, pipeline_id: str, context: dict) -> PipelineRun:
        pipeline = self.repository.get_by_id(pipeline_id)
        if not pipeline:
            raise PipelineNotFoundError(f"Pipeline {pipeline_id} not found")
        
        return self.executor.execute(pipeline, context)
```

#### 3. Factory Pattern pour connecteurs
```python
class ConnectorFactory:
    _connectors = {}
    
    @classmethod
    def register(cls, connector_type: str):
        def decorator(connector_class):
            cls._connectors[connector_type] = connector_class
            return connector_class
        return decorator
    
    @classmethod
    def create(cls, connector_type: str, config: dict) -> BaseConnector:
        if connector_type not in cls._connectors:
            raise ValueError(f"Unknown connector type: {connector_type}")
        return cls._connectors[connector_type](config)

# Usage
@ConnectorFactory.register('postgresql')
class PostgreSQLConnector(BaseConnector):
    pass
```

### Gestion des erreurs

#### Hiérarchie d'exceptions
```python
class ETLPlatformError(Exception):
    """Base exception pour toutes les erreurs de la plateforme"""
    pass

class ConnectorError(ETLPlatformError):
    """Erreurs liées aux connecteurs"""
    pass

class PipelineError(ETLPlatformError):
    """Erreurs d'exécution de pipeline"""
    pass

class ValidationError(ETLPlatformError):
    """Erreurs de validation"""
    pass

# Usage avec contexte
try:
    result = connector.extract()
except ConnectorError as e:
    logger.error(f"Connector failed: {e}", extra={
        'connector_id': connector.id,
        'error_type': type(e).__name__
    })
    raise
```

#### Retry decorator
```python
import functools
import time
import random
from typing import Callable, Type

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    
                    delay = min(
                        base_delay * (2 ** attempt) + random.uniform(0, 1),
                        max_delay
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, exceptions=(ConnectorError,))
def connect_to_database():
    pass
```

## Testing Strategy

### Structure des tests
```
tests/
├── unit/                      # Tests unitaires
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_connectors.py
│   └── test_utils.py
├── integration/               # Tests d'intégration
│   ├── test_pipeline_execution.py
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
├── e2e/                       # Tests end-to-end
│   ├── test_complete_workflows.py
│   └── test_ui_interactions.py
├── fixtures/                  # Données de test
│   ├── connectors.json
│   └── pipelines.json
└── conftest.py               # Configuration pytest
```

### Fixtures et factories
```python
# conftest.py
import pytest
from django.test import TestCase
from factory import Factory, Faker, SubFactory

class UserFactory(Factory):
    class Meta:
        model = User
    
    username = Faker('user_name')
    email = Faker('email')
    first_name = Faker('first_name')

class ConnectorFactory(Factory):
    class Meta:
        model = Connector
    
    name = Faker('name')
    connector_type = 'postgresql'
    created_by = SubFactory(UserFactory)

@pytest.fixture
def sample_pipeline():
    return PipelineFactory()
```

### Tests de performance
```python
import pytest
from django.test import TransactionTestCase
from django.test.utils import override_settings

class PerformanceTestCase(TransactionTestCase):
    
    @override_settings(DEBUG=False)
    def test_pipeline_execution_performance(self):
        """Test que l'exécution d'un pipeline reste sous 30 secondes"""
        start_time = time.time()
        
        # Exécuter pipeline avec 1000 records
        result = execute_large_pipeline()
        
        execution_time = time.time() - start_time
        self.assertLess(execution_time, 30.0)
        self.assertTrue(result.success)
```

## API Development

### Serializers avec validation
```python
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

class PipelineSerializer(serializers.ModelSerializer):
    steps_count = serializers.SerializerMethodField()
    last_run_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'status', 'steps_count', 'last_run_status']
        validators = [
            UniqueTogetherValidator(
                queryset=Pipeline.objects.all(),
                fields=['organization', 'name']
            )
        ]
    
    def get_steps_count(self, obj):
        return obj.steps.count()
    
    def get_last_run_status(self, obj):
        last_run = obj.runs.order_by('-started_at').first()
        return last_run.status if last_run else None
    
    def validate_config(self, value):
        """Validation personnalisée de la configuration"""
        try:
            # Valider contre JSON Schema
            validate_pipeline_config(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
```

### ViewSets avec permissions
```python
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

class PipelineViewSet(viewsets.ModelViewSet):
    serializer_class = PipelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'organization']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    
    def get_queryset(self):
        return Pipeline.objects.filter(
            organization__members=self.request.user
        ).select_related('created_by').prefetch_related('steps')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Lancer l'exécution d'un pipeline"""
        pipeline = self.get_object()
        
        # Vérifier permissions
        if not request.user.has_perm('pipelines.execute_pipeline', pipeline):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Lancer exécution
        try:
            run = PipelineExecutor().execute(pipeline, request.data.get('context', {}))
            return Response({
                'run_id': run.id,
                'status': run.status
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
```

## Debugging et logging

### Configuration logging
```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        'etl_platform': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        }
    }
}
```

### Structured logging
```python
import structlog

logger = structlog.get_logger()

# Usage avec contexte
logger.info(
    "Pipeline execution started",
    pipeline_id=pipeline.id,
    user_id=request.user.id,
    trigger_type="manual"
)

# En cas d'erreur
logger.error(
    "Task execution failed",
    task_id=task.id,
    error_type=type(e).__name__,
    error_message=str(e),
    retry_count=task.retry_count
)
```

## Git Workflow

### Branching strategy
```bash
# Feature branches
git checkout -b feature/add-new-connector
git checkout -b bugfix/fix-memory-leak
git checkout -b hotfix/security-patch

# Convention commits
git commit -m "feat(connectors): add BigQuery connector"
git commit -m "fix(pipelines): resolve DAG cycle detection"
git commit -m "docs(api): update endpoint documentation"
```

### Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: local
    hooks:
      - id: django-check
        name: Django Check
        entry: python manage.py check
        language: system
        pass_filenames: false
```

## Contribution

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new security vulnerabilities
```

### Code Review Guidelines
1. **Sécurité** : Vérifier l'absence de vulnérabilités
2. **Performance** : Identifier les goulots d'étranglement
3. **Maintenabilité** : Code lisible et bien documenté
4. **Tests** : Couverture suffisante et tests pertinents
5. **Architecture** : Respect des patterns établis
