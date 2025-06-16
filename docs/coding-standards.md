# Standards de Code - Django ETL Platform

## Vue d'ensemble

Ce document définit les standards de code, conventions et bonnes pratiques à suivre pour maintenir la cohérence et la qualité du code de la plateforme ETL Django.

## Standards Python

### PEP 8 et extensions

Nous suivons strictement PEP 8 avec quelques extensions spécifiques :

```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations/
  | venv/
  | build/
  | dist/
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["apps", "etl_platform"]
known_django = ["django"]
sections = ["FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503", "E501"]
exclude = ["migrations", "venv", "build", "dist"]
per-file-ignores = [
    "__init__.py:F401",
    "settings/*.py:F405,F403"
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
check_untyped_defs = true
```

### Conventions de nommage

#### Variables et fonctions
```python
# ✅ Bon
user_count = 42
def calculate_average_duration():
    pass

def process_pipeline_data(pipeline_id: str, context: dict) -> bool:
    pass

# ❌ Mauvais
userCount = 42
def calculateAverageDuration():
    pass
```

#### Classes
```python
# ✅ Bon
class PipelineExecutor:
    """Exécuteur de pipelines ETL."""
    pass

class DatabaseConnector:
    """Connecteur de base de données."""
    pass

# ❌ Mauvais  
class pipelineExecutor:
    pass

class database_connector:
    pass
```

#### Constantes
```python
# ✅ Bon
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 30
SUPPORTED_CONNECTOR_TYPES = ['postgresql', 'mysql', 'rest_api']

# ❌ Mauvais
max_retry_count = 3
DefaultTimeoutSeconds = 30
```

#### Variables privées et protégées
```python
class Pipeline:
    def __init__(self):
        self.name = "public"           # Public
        self._status = "protected"     # Protégé (usage interne)
        self.__id = "private"         # Privé (mangling)
    
    def _validate_config(self):       # Méthode protégée
        """Validation interne de la configuration."""
        pass
    
    def __generate_id(self):          # Méthode privée
        """Génération d'ID interne."""
        pass
```

## Documentation du code

### Docstrings

Nous utilisons le style Google pour les docstrings :

```python
def execute_pipeline(pipeline_id: str, context: dict, timeout: int = 3600) -> PipelineRun:
    """Exécute un pipeline ETL.
    
    Args:
        pipeline_id: L'identifiant unique du pipeline à exécuter.
        context: Le contexte d'exécution contenant les paramètres et variables.
        timeout: Le timeout d'exécution en secondes. Défaut: 3600.
        
    Returns:
        Une instance de PipelineRun représentant l'exécution.
        
    Raises:
        PipelineNotFoundError: Si le pipeline n'existe pas.
        ValidationError: Si la configuration est invalide.
        TimeoutError: Si l'exécution dépasse le timeout.
        
    Example:
        >>> context = {'env': 'production', 'batch_size': 1000}
        >>> run = execute_pipeline('pipe-123', context, timeout=1800)
        >>> print(run.status)
        'running'
    """
    pass

class ConnectorFactory:
    """Factory pour créer des instances de connecteurs.
    
    Cette factory utilise le pattern Registry pour maintenir
    un mapping entre les types de connecteurs et leurs classes
    d'implémentation correspondantes.
    
    Attributes:
        _connectors: Dictionnaire des connecteurs enregistrés.
        
    Example:
        >>> factory = ConnectorFactory()
        >>> connector = factory.create('postgresql', config)
        >>> result = connector.test_connection()
    """
    
    def create(self, connector_type: str, config: dict) -> BaseConnector:
        """Crée une instance de connecteur.
        
        Args:
            connector_type: Le type de connecteur ('postgresql', 'mysql', etc.).
            config: La configuration du connecteur.
            
        Returns:
            Une instance du connecteur correspondant.
            
        Raises:
            ValueError: Si le type de connecteur n'est pas supporté.
        """
        pass
```

### Commentaires

```python
# ✅ Bon - Commentaires explicatifs
def calculate_pipeline_metrics(pipeline_id: str) -> dict:
    """Calcule les métriques d'un pipeline."""
    
    # Récupérer les exécutions des 30 derniers jours pour le calcul
    cutoff_date = datetime.now() - timedelta(days=30)
    runs = PipelineRun.objects.filter(
        pipeline_id=pipeline_id,
        started_at__gte=cutoff_date
    )
    
    # Calculer le taux de succès en excluant les exécutions annulées
    total_runs = runs.exclude(status='cancelled').count()
    successful_runs = runs.filter(status='success').count()
    
    return {
        'success_rate': successful_runs / total_runs if total_runs > 0 else 0,
        'total_runs': total_runs
    }

# ❌ Mauvais - Commentaires évidents
def get_user_name(user_id: str) -> str:
    # Récupérer l'utilisateur
    user = User.objects.get(id=user_id)
    # Retourner le nom
    return user.name
```

## Type Hints

### Utilisation obligatoire

```python
from typing import Optional, List, Dict, Union, Tuple, Any
from datetime import datetime

# ✅ Bon - Types explicites
def process_data(
    data: List[Dict[str, Any]], 
    filters: Optional[Dict[str, str]] = None,
    batch_size: int = 1000
) -> Tuple[int, List[str]]:
    """Traite les données par batch."""
    processed_count = 0
    errors: List[str] = []
    
    for batch in chunk_data(data, batch_size):
        try:
            result = apply_filters(batch, filters)
            processed_count += len(result)
        except Exception as e:
            errors.append(str(e))
    
    return processed_count, errors

# ✅ Bon - Classes avec types
class PipelineConfig:
    """Configuration d'un pipeline."""
    
    def __init__(
        self, 
        name: str, 
        schedule: str, 
        timeout: int,
        retry_count: int = 3,
        notifications: Optional[Dict[str, List[str]]] = None
    ) -> None:
        self.name = name
        self.schedule = schedule
        self.timeout = timeout
        self.retry_count = retry_count
        self.notifications = notifications or {}

# ❌ Mauvais - Pas de types
def process_data(data, filters=None, batch_size=1000):
    pass
```

### Types personnalisés

```python
from typing import TypeAlias, Protocol, Generic, TypeVar

# Type aliases pour clarifier le code
PipelineID: TypeAlias = str
ConnectorConfig: TypeAlias = Dict[str, Any]
TaskResult: TypeAlias = Dict[str, Union[str, int, float]]

# Protocols pour duck typing
class Connectable(Protocol):
    """Protocol pour les objets connectables."""
    
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def test_connection(self) -> bool: ...

# Génériques
T = TypeVar('T')

class Repository(Generic[T]):
    """Repository générique."""
    
    def get(self, id: str) -> Optional[T]: ...
    def save(self, entity: T) -> T: ...
    def delete(self, id: str) -> bool: ...
```

## Gestion des erreurs

### Hiérarchie d'exceptions

```python
# exceptions.py
class ETLPlatformError(Exception):
    """Exception de base pour la plateforme ETL."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}

class ConnectorError(ETLPlatformError):
    """Erreurs liées aux connecteurs."""
    pass

class ConnectionError(ConnectorError):
    """Erreur de connexion."""
    pass

class AuthenticationError(ConnectorError):
    """Erreur d'authentification."""
    pass

class PipelineError(ETLPlatformError):
    """Erreurs liées aux pipelines."""
    pass

class ValidationError(PipelineError):
    """Erreur de validation."""
    pass

class ExecutionError(PipelineError):
    """Erreur d'exécution."""
    pass

# Utilisation avec contexte
try:
    connector.connect()
except ConnectionError as e:
    logger.error(
        f"Failed to connect to {connector.name}: {e.message}",
        extra={
            'error_code': e.error_code,
            'connector_type': connector.connector_type,
            'details': e.details
        }
    )
    raise
```

### Gestion des exceptions

```python
# ✅ Bon - Gestion spécifique et logging
def extract_data(connector: BaseConnector, query: str) -> pd.DataFrame:
    """Extrait les données d'un connecteur."""
    try:
        return connector.extract(query)
    except ConnectionError as e:
        logger.error(
            "Database connection failed during extraction",
            extra={
                'connector_id': connector.id,
                'query': query[:100],  # Limiter la taille
                'error': str(e)
            }
        )
        raise
    except TimeoutError as e:
        logger.warning(
            "Query timeout during extraction",
            extra={
                'connector_id': connector.id,
                'timeout_seconds': connector.timeout
            }
        )
        raise
    except Exception as e:
        logger.exception("Unexpected error during extraction")
        raise ExecutionError(f"Extraction failed: {str(e)}")

# ❌ Mauvais - Catch générique
def extract_data(connector, query):
    try:
        return connector.extract(query)
    except Exception as e:
        print(f"Error: {e}")
        return None
```

## Patterns et architecture

### Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class PipelineRepository(ABC):
    """Interface pour l'accès aux données des pipelines."""
    
    @abstractmethod
    def get_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        """Récupère un pipeline par son ID."""
        pass
    
    @abstractmethod
    def get_active_pipelines(self, organization_id: str) -> List[Pipeline]:
        """Récupère les pipelines actifs d'une organisation."""
        pass
    
    @abstractmethod
    def save(self, pipeline: Pipeline) -> Pipeline:
        """Sauvegarde un pipeline."""
        pass

class DjangoPipelineRepository(PipelineRepository):
    """Implémentation Django du repository de pipelines."""
    
    def get_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        """Récupère un pipeline par son ID."""
        try:
            return Pipeline.objects.select_related('organization').get(id=pipeline_id)
        except Pipeline.DoesNotExist:
            return None
    
    def get_active_pipelines(self, organization_id: str) -> List[Pipeline]:
        """Récupère les pipelines actifs d'une organisation."""
        return list(
            Pipeline.objects.filter(
                organization_id=organization_id,
                status='active'
            ).select_related('organization')
        )
    
    def save(self, pipeline: Pipeline) -> Pipeline:
        """Sauvegarde un pipeline."""
        pipeline.save()
        return pipeline
```

### Service Layer

```python
class PipelineService:
    """Service de gestion des pipelines."""
    
    def __init__(self, repository: PipelineRepository, validator: PipelineValidator):
        self._repository = repository
        self._validator = validator
    
    def create_pipeline(self, data: dict, user: User) -> Pipeline:
        """Crée un nouveau pipeline."""
        # Validation
        self._validator.validate_creation_data(data)
        
        # Création
        pipeline = Pipeline(
            name=data['name'],
            description=data.get('description', ''),
            organization=user.current_organization,
            created_by=user,
            config=data.get('config', {})
        )
        
        # Sauvegarde
        return self._repository.save(pipeline)
    
    def execute_pipeline(self, pipeline_id: str, context: dict, user: User) -> PipelineRun:
        """Exécute un pipeline."""
        pipeline = self._repository.get_by_id(pipeline_id)
        if not pipeline:
            raise ValidationError(f"Pipeline {pipeline_id} not found")
        
        # Vérifier les permissions
        if not user.can_execute_pipeline(pipeline):
            raise PermissionError("Insufficient permissions to execute pipeline")
        
        # Lancer l'exécution
        executor = PipelineExecutor()
        return executor.execute(pipeline, context, user)
```

## Tests et qualité

### Conventions de tests

```python
# tests/unit/test_pipeline_service.py
import pytest
from unittest.mock import Mock, patch
from apps.pipelines.services import PipelineService
from apps.pipelines.models import Pipeline
from tests.factories import UserFactory, PipelineFactory

class TestPipelineService:
    """Tests du service Pipeline."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock du repository."""
        return Mock()
    
    @pytest.fixture
    def mock_validator(self):
        """Mock du validator."""
        validator = Mock()
        validator.validate_creation_data.return_value = None
        return validator
    
    @pytest.fixture
    def service(self, mock_repository, mock_validator):
        """Instance du service à tester."""
        return PipelineService(mock_repository, mock_validator)
    
    def test_create_pipeline_success(self, service, mock_repository):
        """Test création réussie d'un pipeline."""
        # Given
        user = UserFactory()
        data = {
            'name': 'Test Pipeline',
            'description': 'Test description',
            'config': {'schedule': '0 2 * * *'}
        }
        expected_pipeline = PipelineFactory.build()
        mock_repository.save.return_value = expected_pipeline
        
        # When
        result = service.create_pipeline(data, user)
        
        # Then
        assert result == expected_pipeline
        mock_repository.save.assert_called_once()
        
    def test_create_pipeline_validation_error(self, service, mock_validator):
        """Test création avec erreur de validation."""
        # Given
        user = UserFactory()
        data = {'name': ''}  # Nom vide invalide
        mock_validator.validate_creation_data.side_effect = ValidationError("Name required")
        
        # When/Then
        with pytest.raises(ValidationError, match="Name required"):
            service.create_pipeline(data, user)
```

### Factories pour les tests

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.core.models import User, Organization
from apps.pipelines.models import Pipeline

class UserFactory(DjangoModelFactory):
    """Factory pour créer des utilisateurs de test."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

class OrganizationFactory(DjangoModelFactory):
    """Factory pour créer des organisations de test."""
    
    class Meta:
        model = Organization
    
    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))

class PipelineFactory(DjangoModelFactory):
    """Factory pour créer des pipelines de test."""
    
    class Meta:
        model = Pipeline
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)
    status = 'active'
    config = factory.LazyFunction(lambda: {
        'schedule': '0 2 * * *',
        'timeout': 3600,
        'retry_count': 3
    })
```

## Configuration et environnements

### Settings modulaires

```python
# settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.core',
    'apps.connectors',
    'apps.pipelines',
    'apps.tasks',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'etl_platform_dev',
        'USER': 'etl_user',
        'PASSWORD': 'etl_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# settings/production.py
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### Variables d'environnement

```python
# utils/env.py
import os
from typing import Any, Optional

def get_env_variable(var_name: str, default: Any = None, required: bool = False) -> Any:
    """Récupère une variable d'environnement avec validation."""
    value = os.getenv(var_name, default)
    
    if required and value is None:
        raise EnvironmentError(f"Required environment variable {var_name} is not set")
    
    return value

def get_bool_env(var_name: str, default: bool = False) -> bool:
    """Récupère une variable d'environnement booléenne."""
    value = get_env_variable(var_name, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')

def get_int_env(var_name: str, default: Optional[int] = None) -> Optional[int]:
    """Récupère une variable d'environnement entière."""
    value = get_env_variable(var_name, default)
    if value is None:
        return None
    return int(value)

# Utilisation
DEBUG = get_bool_env('DEBUG', False)
DATABASE_URL = get_env_variable('DATABASE_URL', required=True)
MAX_WORKERS = get_int_env('MAX_WORKERS', 4)
```

## Sécurité

### Validation des entrées

```python
from django.core.exceptions import ValidationError
from typing import Any, Dict

def validate_pipeline_config(config: Dict[str, Any]) -> None:
    """Valide la configuration d'un pipeline."""
    required_fields = ['schedule', 'timeout']
    
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validation du schedule (cron expression)
    schedule = config['schedule']
    if not isinstance(schedule, str) or len(schedule.split()) != 5:
        raise ValidationError("Invalid cron expression for schedule")
    
    # Validation du timeout
    timeout = config['timeout']
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValidationError("Timeout must be a positive integer")
    
    # Validation optionnelle
    if 'retry_count' in config:
        retry_count = config['retry_count']
        if not isinstance(retry_count, int) or retry_count < 0:
            raise ValidationError("Retry count must be a non-negative integer")
```

### Sanitisation des données

```python
import re
from html import escape

def sanitize_user_input(input_str: str) -> str:
    """Sanitise une entrée utilisateur."""
    if not isinstance(input_str, str):
        return str(input_str)
    
    # Échapper les caractères HTML
    sanitized = escape(input_str)
    
    # Supprimer les caractères de contrôle
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    
    return sanitized.strip()

def validate_sql_query(query: str) -> bool:
    """Valide qu'une requête SQL est safe (lecture seule)."""
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
        'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE'
    ]
    
    query_upper = query.upper().strip()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False
    
    return query_upper.startswith('SELECT')
```

## Performance

### Optimisations Django

```python
# Utilisation efficace de l'ORM
def get_pipelines_with_metrics(organization_id: str) -> List[Dict]:
    """Récupère les pipelines avec leurs métriques de façon optimisée."""
    
    # ✅ Bon - Une seule requête avec aggregation
    from django.db.models import Count, Avg, Q
    
    pipelines = Pipeline.objects.filter(
        organization_id=organization_id
    ).select_related(
        'organization', 'created_by'
    ).prefetch_related(
        'steps'
    ).annotate(
        total_runs=Count('runs'),
        successful_runs=Count('runs', filter=Q(runs__status='success')),
        avg_duration=Avg('runs__duration')
    )
    
    return [
        {
            'id': p.id,
            'name': p.name,
            'total_runs': p.total_runs,
            'success_rate': p.successful_runs / p.total_runs if p.total_runs > 0 else 0,
            'avg_duration': p.avg_duration or 0
        }
        for p in pipelines
    ]

# ❌ Mauvais - N+1 queries
def get_pipelines_with_metrics_bad(organization_id: str) -> List[Dict]:
    pipelines = Pipeline.objects.filter(organization_id=organization_id)
    
    result = []
    for pipeline in pipelines:  # Query pour chaque pipeline
        runs = pipeline.runs.all()  # N+1 query
        total_runs = runs.count()
        successful_runs = runs.filter(status='success').count()
        
        result.append({
            'id': pipeline.id,
            'name': pipeline.name,
            'total_runs': total_runs,
            'success_rate': successful_runs / total_runs if total_runs > 0 else 0
        })
    
    return result
```

### Cache efficace

```python
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
import hashlib

def cache_pipeline_metrics(pipeline_id: str, time_window: int = 3600) -> Dict:
    """Cache les métriques d'un pipeline avec invalidation intelligente."""
    
    # Clé de cache basée sur les paramètres et la dernière modification
    pipeline = Pipeline.objects.get(id=pipeline_id)
    cache_key = f"pipeline_metrics:{pipeline_id}:{pipeline.updated_at.timestamp()}"
    
    # Essayer de récupérer depuis le cache
    metrics = cache.get(cache_key)
    
    if metrics is None:
        # Calculer les métriques
        metrics = calculate_pipeline_metrics(pipeline_id)
        
        # Mettre en cache avec TTL
        cache.set(cache_key, metrics, timeout=time_window)
    
    return metrics

def invalidate_pipeline_cache(pipeline_id: str) -> None:
    """Invalide le cache d'un pipeline."""
    pattern = f"pipeline_metrics:{pipeline_id}:*"
    cache.delete_pattern(pattern)
```

Ces standards de code garantissent la maintienabilité, la lisibilité et la performance du code de la plateforme ETL Django.
