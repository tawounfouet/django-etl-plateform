# Tests et Stratégie Qualité - Django ETL Platform

## Stratégie de test globale

### Pyramide de tests

```
                    /\
                   /  \
                  / E2E \
                 /Tests \
                /________\
               /          \
              / Integration \
             /    Tests     \
            /________________\
           /                  \
          /    Unit Tests      \
         /____________________\
```

Notre stratégie suit la pyramide de tests avec :
- **70% Tests unitaires** : Rapides, isolés, testent la logique métier
- **20% Tests d'intégration** : Testent les interactions entre composants
- **10% Tests E2E** : Testent les workflows complets utilisateur

## Configuration de test

### Structure des tests

```
tests/
├── __init__.py
├── conftest.py                 # Configuration pytest globale
├── fixtures/                   # Données de test
│   ├── connectors.json
│   ├── pipelines.json
│   └── sample_data.csv
├── unit/                       # Tests unitaires
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_services.py
│   ├── connectors/
│   │   ├── test_base_connector.py
│   │   ├── test_postgresql.py
│   │   └── test_rest_api.py
│   ├── pipelines/
│   │   ├── test_pipeline_builder.py
│   │   ├── test_dag_generator.py
│   │   └── test_validators.py
│   └── tasks/
│       ├── test_extract_tasks.py
│       ├── test_transform_tasks.py
│       └── test_load_tasks.py
├── integration/                # Tests d'intégration
│   ├── __init__.py
│   ├── test_pipeline_execution.py
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_celery_tasks.py
├── e2e/                        # Tests end-to-end
│   ├── __init__.py
│   ├── test_complete_workflows.py
│   ├── test_ui_interactions.py
│   └── test_api_flows.py
├── performance/                # Tests de performance
│   ├── __init__.py
│   ├── test_large_datasets.py
│   ├── test_concurrent_pipelines.py
│   └── test_memory_usage.py
└── security/                   # Tests de sécurité
    ├── __init__.py
    ├── test_authentication.py
    ├── test_authorization.py
    └── test_data_encryption.py
```

### Configuration pytest

```python
# conftest.py
import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line
import factory
from unittest.mock import Mock, patch

# Configuration Django pour les tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etl_platform.settings.test')
django.setup()

# Fixtures globales
@pytest.fixture(scope='session')
def django_db_setup():
    """Setup de la base de données de test"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_etl_platform',
        'USER': 'test_user',
        'PASSWORD': 'test_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }

@pytest.fixture
def api_client():
    """Client API pour les tests"""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_user():
    """Utilisateur authentifié pour les tests"""
    from apps.core.models import User
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user

@pytest.fixture
def authenticated_api_client(api_client, authenticated_user):
    """Client API avec utilisateur authentifié"""
    api_client.force_authenticate(user=authenticated_user)
    return api_client

@pytest.fixture
def sample_organization():
    """Organisation de test"""
    from apps.core.models import Organization
    return Organization.objects.create(
        name='Test Organization',
        slug='test-org'
    )

@pytest.fixture
def mock_connector():
    """Mock connector pour les tests"""
    connector = Mock()
    connector.test_connection.return_value = True
    connector.extract.return_value = iter([])
    connector.load.return_value = True
    return connector

@pytest.fixture
def celery_app():
    """Application Celery pour les tests"""
    from etl_platform.celery_app import app
    app.conf.update(CELERY_ALWAYS_EAGER=True)
    return app

# Factory classes pour les tests
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.User'
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.Organization'
    
    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))

class ConnectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'connectors.Connector'
    
    name = factory.Faker('word')
    connector_type = 'postgresql'
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)
    config = factory.LazyFunction(lambda: {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db'
    })

class PipelineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'pipelines.Pipeline'
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text')
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)
    status = 'active'
    config = factory.LazyFunction(lambda: {
        'schedule': '0 2 * * *',  # Daily at 2 AM
        'timeout': 3600
    })
```

## Tests unitaires

### Tests des modèles

```python
# tests/unit/test_models.py
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.pipelines.models import Pipeline, PipelineStep
from apps.connectors.models import Connector
from conftest import UserFactory, OrganizationFactory, ConnectorFactory, PipelineFactory

@pytest.mark.django_db
class TestPipelineModel:
    """Tests du modèle Pipeline"""
    
    def test_pipeline_creation(self):
        """Test création basique d'un pipeline"""
        pipeline = PipelineFactory()
        assert pipeline.id is not None
        assert pipeline.name is not None
        assert pipeline.status == 'active'
    
    def test_pipeline_unique_name_per_organization(self):
        """Test unicité du nom par organisation"""
        org = OrganizationFactory()
        pipeline1 = PipelineFactory(name='Test Pipeline', organization=org)
        
        with pytest.raises(IntegrityError):
            PipelineFactory(name='Test Pipeline', organization=org)
    
    def test_pipeline_str_representation(self):
        """Test représentation string du pipeline"""
        pipeline = PipelineFactory(name='Test Pipeline')
        assert str(pipeline) == 'Test Pipeline'
    
    def test_pipeline_get_absolute_url(self):
        """Test génération URL absolue"""
        pipeline = PipelineFactory()
        expected_url = f'/pipelines/{pipeline.id}/'
        assert pipeline.get_absolute_url() == expected_url
    
    def test_pipeline_steps_ordering(self):
        """Test ordonnancement des étapes"""
        pipeline = PipelineFactory()
        
        step3 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Step 3',
            order_index=3,
            step_type='load',
            config={}
        )
        step1 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Step 1',
            order_index=1,
            step_type='extract',
            config={}
        )
        step2 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Step 2',
            order_index=2,
            step_type='transform',
            config={}
        )
        
        steps = list(pipeline.steps.all())
        assert steps[0] == step1
        assert steps[1] == step2
        assert steps[2] == step3

@pytest.mark.django_db
class TestConnectorModel:
    """Tests du modèle Connector"""
    
    def test_connector_encryption_credentials(self):
        """Test chiffrement des credentials"""
        connector = ConnectorFactory()
        
        # Tester que les credentials sont chiffrés
        credentials = {
            'username': 'testuser',
            'password': 'secret123'
        }
        
        connector.credential.encrypt_data(credentials)
        connector.credential.save()
        
        # Vérifier que les données sont chiffrées
        assert connector.credential.encrypted_data != str(credentials)
        
        # Vérifier le déchiffrement
        decrypted = connector.credential.decrypt_data()
        assert decrypted == credentials
    
    def test_connector_test_connection_method(self):
        """Test méthode test_connection"""
        connector = ConnectorFactory()
        
        with patch('apps.connectors.models.ConnectorFactory.create') as mock_create:
            mock_instance = Mock()
            mock_instance.test_connection.return_value = True
            mock_create.return_value = mock_instance
            
            result = connector.test_connection()
            assert result is True
            mock_create.assert_called_once()
```

### Tests des connecteurs

```python
# tests/unit/connectors/test_postgresql.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from apps.connectors.database.postgresql import PostgreSQLConnector
from apps.connectors.base import ConnectionConfig

class TestPostgreSQLConnector:
    """Tests du connecteur PostgreSQL"""
    
    @pytest.fixture
    def config(self):
        return ConnectionConfig(
            connector_type='postgresql',
            name='Test PostgreSQL',
            config={
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'schema': 'public'
            },
            credentials={
                'username': 'testuser',
                'password': 'testpass'
            }
        )
    
    @pytest.fixture
    def connector(self, config):
        return PostgreSQLConnector(config)
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_connect_success(self, mock_pool, connector):
        """Test connexion réussie"""
        mock_pool_instance = Mock()
        mock_pool.return_value = mock_pool_instance
        
        connector.connect()
        
        assert connector.connection_pool == mock_pool_instance
        mock_pool.assert_called_once()
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_connect_failure(self, mock_pool, connector):
        """Test échec de connexion"""
        mock_pool.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            connector.connect()
    
    def test_test_connection_success(self, connector):
        """Test test_connection avec succès"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(connector, 'get_connection', return_value=mock_conn):
            with patch.object(connector, 'return_connection'):
                result = connector.test_connection()
                
                assert result is True
                mock_cursor.execute.assert_called_once_with("SELECT 1")
    
    def test_extract_with_chunks(self, connector):
        """Test extraction par chunks"""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Simuler des données en chunks
        mock_cursor.fetchmany.side_effect = [
            [('row1_col1', 'row1_col2'), ('row2_col1', 'row2_col2')],  # Premier chunk
            [('row3_col1', 'row3_col2')],  # Deuxième chunk
            []  # Fin des données
        ]
        mock_cursor.description = [('col1',), ('col2',)]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(connector, 'get_connection', return_value=mock_conn):
            with patch.object(connector, 'return_connection'):
                
                chunks = list(connector.extract("SELECT * FROM test_table", chunk_size=2))
                
                assert len(chunks) == 2
                assert len(chunks[0]) == 2  # Premier chunk avec 2 lignes
                assert len(chunks[1]) == 1  # Deuxième chunk avec 1 ligne
                assert list(chunks[0].columns) == ['col1', 'col2']
    
    def test_load_append_mode(self, connector):
        """Test chargement en mode append"""
        data = pd.DataFrame({
            'col1': ['value1', 'value2'],
            'col2': ['value3', 'value4']
        })
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch.object(connector, 'get_connection', return_value=mock_conn):
            with patch.object(connector, 'return_connection'):
                with patch.object(connector, '_bulk_insert') as mock_bulk_insert:
                    
                    result = connector.load(data, 'test_table', mode='append')
                    
                    assert result is True
                    mock_bulk_insert.assert_called_once()
                    mock_conn.commit.assert_called_once()
    
    def test_upsert_mode(self, connector):
        """Test mode upsert"""
        data = pd.DataFrame({
            'id': [1, 2],
            'name': ['John', 'Jane'],
            'email': ['john@test.com', 'jane@test.com']
        })
        
        mock_conn = Mock()
        
        with patch.object(connector, 'get_connection', return_value=mock_conn):
            with patch.object(connector, 'return_connection'):
                with patch.object(connector, '_upsert_data', return_value=True) as mock_upsert:
                    
                    result = connector.load(data, 'users', mode='upsert', upsert_key='id')
                    
                    assert result is True
                    mock_upsert.assert_called_once_with(mock_conn, data, 'public.users', 'id')
```

### Tests des services

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from apps.pipelines.services import PipelineService, PipelineExecutionService
from apps.pipelines.models import Pipeline, PipelineRun
from conftest import PipelineFactory, UserFactory

@pytest.mark.django_db
class TestPipelineService:
    """Tests du service Pipeline"""
    
    @pytest.fixture
    def pipeline_service(self):
        return PipelineService()
    
    def test_create_pipeline(self, pipeline_service):
        """Test création de pipeline"""
        user = UserFactory()
        pipeline_data = {
            'name': 'Test Pipeline',
            'description': 'Test Description',
            'config': {'schedule': '0 2 * * *'}
        }
        
        pipeline = pipeline_service.create_pipeline(user, pipeline_data)
        
        assert pipeline.name == 'Test Pipeline'
        assert pipeline.created_by == user
        assert pipeline.config['schedule'] == '0 2 * * *'
    
    def test_validate_pipeline_config(self, pipeline_service):
        """Test validation de configuration"""
        valid_config = {
            'schedule': '0 2 * * *',
            'timeout': 3600,
            'retry_count': 3
        }
        
        assert pipeline_service.validate_config(valid_config) is True
        
        invalid_config = {
            'schedule': 'invalid cron',
            'timeout': -1
        }
        
        assert pipeline_service.validate_config(invalid_config) is False
    
    def test_get_pipeline_metrics(self, pipeline_service):
        """Test récupération des métriques"""
        pipeline = PipelineFactory()
        
        with patch.object(pipeline_service, '_calculate_success_rate', return_value=0.85):
            with patch.object(pipeline_service, '_calculate_avg_duration', return_value=300):
                
                metrics = pipeline_service.get_pipeline_metrics(pipeline.id)
                
                assert metrics['success_rate'] == 0.85
                assert metrics['avg_duration'] == 300

@pytest.mark.django_db  
class TestPipelineExecutionService:
    """Tests du service d'exécution de pipeline"""
    
    @pytest.fixture
    def execution_service(self):
        return PipelineExecutionService()
    
    def test_execute_pipeline(self, execution_service):
        """Test exécution de pipeline"""
        pipeline = PipelineFactory()
        user = UserFactory()
        context = {'param1': 'value1'}
        
        with patch.object(execution_service, '_create_pipeline_run') as mock_create_run:
            with patch.object(execution_service, '_execute_steps') as mock_execute_steps:
                
                mock_run = Mock()
                mock_run.id = 'test-run-id'
                mock_create_run.return_value = mock_run
                
                run_id = execution_service.execute_pipeline(pipeline, user, context)
                
                assert run_id == 'test-run-id'
                mock_create_run.assert_called_once_with(pipeline, user, context)
                mock_execute_steps.assert_called_once_with(mock_run)
    
    def test_validate_pipeline_dependencies(self, execution_service):
        """Test validation des dépendances"""
        pipeline = PipelineFactory()
        
        # Créer des steps avec dépendances
        from apps.pipelines.models import PipelineStep
        
        step1 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Extract',
            order_index=1,
            step_type='extract',
            config={},
            dependencies=[]
        )
        
        step2 = PipelineStep.objects.create(
            pipeline=pipeline,
            name='Transform',
            order_index=2,
            step_type='transform',
            config={},
            dependencies=[str(step1.id)]
        )
        
        assert execution_service.validate_dependencies(pipeline) is True
        
        # Créer une dépendance circulaire
        step1.dependencies = [str(step2.id)]
        step1.save()
        
        assert execution_service.validate_dependencies(pipeline) is False
```

## Tests d'intégration

### Tests d'API

```python
# tests/integration/test_api_endpoints.py
import pytest
import json
from django.urls import reverse
from rest_framework import status
from conftest import UserFactory, OrganizationFactory, PipelineFactory

@pytest.mark.django_db
class TestPipelineAPI:
    """Tests d'intégration de l'API Pipeline"""
    
    def test_list_pipelines(self, authenticated_api_client):
        """Test listage des pipelines"""
        user = authenticated_api_client.handler._force_user
        org = OrganizationFactory()
        user.organizations.add(org)
        
        # Créer quelques pipelines
        pipeline1 = PipelineFactory(organization=org)
        pipeline2 = PipelineFactory(organization=org)
        
        url = reverse('pipeline-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['results']) == 2
        
        pipeline_names = [p['name'] for p in data['results']]
        assert pipeline1.name in pipeline_names
        assert pipeline2.name in pipeline_names
    
    def test_create_pipeline(self, authenticated_api_client):
        """Test création de pipeline via API"""
        user = authenticated_api_client.handler._force_user
        org = OrganizationFactory()
        user.organizations.add(org)
        
        pipeline_data = {
            'name': 'API Test Pipeline',
            'description': 'Created via API',
            'organization': str(org.id),
            'config': {
                'schedule': '0 3 * * *',
                'timeout': 1800
            }
        }
        
        url = reverse('pipeline-list')
        response = authenticated_api_client.post(
            url, 
            data=json.dumps(pipeline_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == 'API Test Pipeline'
        assert data['organization'] == str(org.id)
    
    def test_execute_pipeline_endpoint(self, authenticated_api_client):
        """Test endpoint d'exécution de pipeline"""
        user = authenticated_api_client.handler._force_user
        pipeline = PipelineFactory(created_by=user)
        
        execution_context = {
            'env': 'test',
            'parameters': {'batch_size': 1000}
        }
        
        url = reverse('pipeline-execute', kwargs={'pk': pipeline.id})
        
        with patch('apps.pipelines.services.PipelineExecutionService.execute_pipeline') as mock_execute:
            mock_execute.return_value = 'test-run-id'
            
            response = authenticated_api_client.post(
                url,
                data=json.dumps({'context': execution_context}),
                content_type='application/json'
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert 'run_id' in data
            mock_execute.assert_called_once()
    
    def test_pipeline_permissions(self, api_client):
        """Test permissions des endpoints pipeline"""
        pipeline = PipelineFactory()
        
        # Test sans authentification
        url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test avec utilisateur non autorisé
        other_user = UserFactory()
        api_client.force_authenticate(user=other_user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Pas accès à l'org
```

### Tests d'exécution de tâches

```python
# tests/integration/test_celery_tasks.py
import pytest
from unittest.mock import patch, Mock
from celery import current_app
from apps.tasks.extract import extract_data_task
from apps.tasks.transform import transform_data_task
from apps.tasks.load import load_data_task
from conftest import ConnectorFactory, PipelineFactory

@pytest.mark.django_db
class TestCeleryTasks:
    """Tests d'intégration des tâches Celery"""
    
    def test_extract_data_task(self, celery_app):
        """Test tâche d'extraction"""
        connector = ConnectorFactory()
        
        task_config = {
            'connector_id': str(connector.id),
            'query': 'SELECT * FROM test_table',
            'chunk_size': 1000
        }
        
        with patch('apps.connectors.models.Connector.get_instance') as mock_get_instance:
            mock_connector_instance = Mock()
            mock_connector_instance.extract.return_value = iter([
                pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
            ])
            mock_get_instance.return_value = mock_connector_instance
            
            result = extract_data_task.apply(args=[task_config])
            
            assert result.successful()
            assert 'extracted_rows' in result.result
            mock_connector_instance.extract.assert_called_once()
    
    def test_transform_data_task(self, celery_app):
        """Test tâche de transformation"""
        transform_config = {
            'input_data': [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}],
            'transformations': [
                {
                    'type': 'rename_columns',
                    'mapping': {'col1': 'id', 'col2': 'name'}
                },
                {
                    'type': 'filter_rows',
                    'condition': 'id > 1'
                }
            ]
        }
        
        result = transform_data_task.apply(args=[transform_config])
        
        assert result.successful()
        transformed_data = result.result['transformed_data']
        assert len(transformed_data) == 1
        assert transformed_data[0]['id'] == 2
        assert transformed_data[0]['name'] == 'b'
    
    def test_load_data_task(self, celery_app):
        """Test tâche de chargement"""
        connector = ConnectorFactory()
        
        load_config = {
            'connector_id': str(connector.id),
            'destination': 'target_table',
            'data': [{'id': 1, 'name': 'test'}],
            'load_mode': 'append'
        }
        
        with patch('apps.connectors.models.Connector.get_instance') as mock_get_instance:
            mock_connector_instance = Mock()
            mock_connector_instance.load.return_value = True
            mock_get_instance.return_value = mock_connector_instance
            
            result = load_data_task.apply(args=[load_config])
            
            assert result.successful()
            assert result.result['loaded_rows'] == 1
            mock_connector_instance.load.assert_called_once()
    
    def test_task_retry_mechanism(self, celery_app):
        """Test mécanisme de retry des tâches"""
        connector = ConnectorFactory()
        
        task_config = {
            'connector_id': str(connector.id),
            'query': 'SELECT * FROM test_table'
        }
        
        with patch('apps.connectors.models.Connector.get_instance') as mock_get_instance:
            # Simuler des échecs puis succès
            mock_connector_instance = Mock()
            mock_connector_instance.extract.side_effect = [
                Exception("Connection timeout"),  # Premier essai échoue
                Exception("Connection timeout"),  # Deuxième essai échoue
                iter([pd.DataFrame({'col1': [1]})])  # Troisième essai réussit
            ]
            mock_get_instance.return_value = mock_connector_instance
            
            result = extract_data_task.apply(args=[task_config])
            
            assert result.successful()
            assert mock_connector_instance.extract.call_count == 3
```

## Tests end-to-end

### Tests de workflows complets

```python
# tests/e2e/test_complete_workflows.py
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from conftest import UserFactory, OrganizationFactory

@pytest.mark.django_db
class TestCompleteETLWorkflow(StaticLiveServerTestCase):
    """Tests end-to-end du workflow ETL complet"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configuration du driver Selenium
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.selenium = webdriver.Chrome(options=options)
        cls.selenium.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def setUp(self):
        self.user = UserFactory(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        self.org = OrganizationFactory(name='Test Organization')
        self.user.organizations.add(self.org)
    
    def test_complete_pipeline_creation_and_execution(self):
        """Test création et exécution complète d'un pipeline"""
        
        # 1. Login
        self.selenium.get(f'{self.live_server_url}/login/')
        
        username_input = self.selenium.find_element(By.NAME, "username")
        password_input = self.selenium.find_element(By.NAME, "password")
        
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')
        
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Vérifier redirection vers dashboard
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/dashboard/')
        )
        
        # 2. Créer un connecteur
        self.selenium.get(f'{self.live_server_url}/connectors/create/')
        
        # Remplir le formulaire de connecteur
        name_input = self.selenium.find_element(By.NAME, "name")
        name_input.send_keys('Test PostgreSQL Connector')
        
        type_select = self.selenium.find_element(By.NAME, "connector_type")
        type_select.send_keys('postgresql')
        
        config_textarea = self.selenium.find_element(By.NAME, "config")
        config_textarea.send_keys('{"host": "localhost", "database": "test_db"}')
        
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Vérifier création du connecteur
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        
        # 3. Créer un pipeline
        self.selenium.get(f'{self.live_server_url}/pipelines/create/')
        
        pipeline_name = self.selenium.find_element(By.NAME, "name")
        pipeline_name.send_keys('Test ETL Pipeline')
        
        description = self.selenium.find_element(By.NAME, "description")
        description.send_keys('Complete ETL workflow test')
        
        # Ajouter des étapes
        add_step_button = self.selenium.find_element(By.ID, "add-step-button")
        add_step_button.click()
        
        # Étape d'extraction
        step_name = self.selenium.find_element(By.NAME, "steps[0][name]")
        step_name.send_keys('Extract Data')
        
        step_type = self.selenium.find_element(By.NAME, "steps[0][step_type]")
        step_type.send_keys('extract')
        
        # Sauvegarder le pipeline
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Vérifier création du pipeline
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/pipelines/')
        )
        
        # 4. Exécuter le pipeline
        execute_button = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, "execute-pipeline-button"))
        )
        execute_button.click()
        
        # Confirmer l'exécution
        confirm_button = self.selenium.find_element(By.ID, "confirm-execution")
        confirm_button.click()
        
        # Vérifier démarrage de l'exécution
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "execution-status"))
        )
        
        # Attendre que l'exécution se termine (ou timeout)
        max_wait = 60  # 60 secondes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_element = self.selenium.find_element(By.CLASS_NAME, "execution-status")
            status_text = status_element.text
            
            if status_text in ['SUCCESS', 'FAILED']:
                break
                
            time.sleep(2)
            self.selenium.refresh()
        
        # Vérifier le résultat final
        final_status = self.selenium.find_element(By.CLASS_NAME, "execution-status")
        assert final_status.text in ['SUCCESS', 'FAILED']  # Au moins terminé
        
        # 5. Vérifier les logs
        logs_tab = self.selenium.find_element(By.ID, "logs-tab")
        logs_tab.click()
        
        logs_content = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, "logs-content"))
        )
        
        assert logs_content.text != ""  # Logs non vides
```

## Tests de performance

### Tests de charge

```python
# tests/performance/test_large_datasets.py
import pytest
import pandas as pd
import time
from unittest.mock import patch
from apps.connectors.database.postgresql import PostgreSQLConnector
from apps.tasks.extract import extract_data_task

@pytest.mark.performance
class TestPerformanceTests:
    """Tests de performance et scalabilité"""
    
    def test_large_dataset_extraction(self, mock_connector):
        """Test extraction de gros dataset"""
        # Simuler un gros dataset (1M records)
        large_data_chunks = []
        chunk_size = 10000
        total_rows = 1000000
        
        for i in range(0, total_rows, chunk_size):
            chunk_data = {
                'id': range(i, min(i + chunk_size, total_rows)),
                'name': [f'name_{j}' for j in range(i, min(i + chunk_size, total_rows))],
                'value': [j * 2 for j in range(i, min(i + chunk_size, total_rows))]
            }
            large_data_chunks.append(pd.DataFrame(chunk_data))
        
        mock_connector.extract.return_value = iter(large_data_chunks)
        
        start_time = time.time()
        
        total_processed = 0
        for chunk in mock_connector.extract("SELECT * FROM large_table"):
            total_processed += len(chunk)
            # Simuler un traitement léger
            chunk['processed'] = chunk['value'] * 2
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assertions de performance
        assert total_processed == total_rows
        assert duration < 30.0  # Moins de 30 secondes
        
        # Calcul du throughput
        throughput = total_processed / duration
        assert throughput > 50000  # Plus de 50K rows/sec
        
        print(f"Processed {total_processed} rows in {duration:.2f}s")
        print(f"Throughput: {throughput:.0f} rows/sec")
    
    def test_concurrent_pipeline_execution(self):
        """Test exécution simultanée de multiples pipelines"""
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        def execute_pipeline(pipeline_id):
            """Simule l'exécution d'un pipeline"""
            start_time = time.time()
            
            # Simuler charge de travail
            time.sleep(0.1)  # Simulation I/O
            
            # Calcul factice
            result = sum(range(10000))
            
            duration = time.time() - start_time
            return {
                'pipeline_id': pipeline_id,
                'duration': duration,
                'result': result
            }
        
        # Lancer 10 pipelines en parallèle
        num_pipelines = 10
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(execute_pipeline, f'pipeline_{i}')
                for i in range(num_pipelines)
            ]
            
            results = [future.result() for future in futures]
        
        total_duration = time.time() - start_time
        
        # Vérifications
        assert len(results) == num_pipelines
        assert all(r['result'] == 49995000 for r in results)  # Vérifier calcul
        
        # Performance: exécution parallèle doit être plus rapide que séquentielle
        sequential_time = sum(r['duration'] for r in results)
        parallelization_efficiency = sequential_time / total_duration
        
        assert parallelization_efficiency > 2.0  # Au moins 2x plus rapide
        
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Parallel time: {total_duration:.2f}s")
        print(f"Efficiency: {parallelization_efficiency:.1f}x")
    
    @pytest.mark.memory
    def test_memory_usage_large_pipeline(self):
        """Test utilisation mémoire pour gros pipeline"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simuler traitement de données volumineuses
        large_datasets = []
        
        try:
            for i in range(100):  # 100 datasets
                # Créer dataset de 10K rows
                data = pd.DataFrame({
                    'col1': range(10000),
                    'col2': [f'string_{j}' for j in range(10000)],
                    'col3': [j * 1.5 for j in range(10000)]
                })
                
                # Simuler transformation
                data['transformed'] = data['col1'] * data['col3']
                large_datasets.append(data)
                
                # Vérifier mémoire périodiquement
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    # Ne pas dépasser 500MB d'augmentation
                    assert memory_increase < 500, f"Memory usage too high: {memory_increase:.1f}MB"
        
        finally:
            # Nettoyer
            del large_datasets
            
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Total increase: {total_increase:.1f}MB")
```

## Tests de sécurité

### Tests d'authentification et autorisation

```python
# tests/security/test_authentication.py
import pytest
from django.test import TestCase
from django.contrib.auth import authenticate
from rest_framework.test import APIClient
from rest_framework import status
from conftest import UserFactory, OrganizationFactory, PipelineFactory

@pytest.mark.django_db
class TestAuthenticationSecurity:
    """Tests de sécurité pour l'authentification"""
    
    def test_password_strength_requirements(self):
        """Test exigences de robustesse du mot de passe"""
        from apps.core.validators import validate_password_strength
        
        # Mots de passe faibles
        weak_passwords = [
            '123456',
            'password',
            'qwerty',
            'abc123',
            '12345678'
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                validate_password_strength(password)
        
        # Mots de passe forts
        strong_passwords = [
            'MyStr0ng!Password',
            'C0mplex&Secure123',
            'V3ry$ecure2023!'
        ]
        
        for password in strong_passwords:
            # Ne doit pas lever d'exception
            validate_password_strength(password)
    
    def test_brute_force_protection(self):
        """Test protection contre force brute"""
        client = APIClient()
        
        # Tenter plusieurs connexions échouées
        for attempt in range(6):  # Limite: 5 tentatives
            response = client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            
            if attempt < 5:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            else:
                # Après 5 échecs, compte temporairement bloqué
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_session_timeout(self):
        """Test timeout de session"""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Simulation d'une session expirée
        with patch('django.contrib.sessions.backends.base.SessionBase.get_expiry_age', return_value=-1):
            response = client.get('/api/pipelines/')
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_jwt_token_security(self):
        """Test sécurité des tokens JWT"""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Vérifier que le token est valide
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = client.get('/api/user/profile/')
        assert response.status_code == status.HTTP_200_OK
        
        # Tester token modifié (invalide)
        tampered_token = str(access_token)[:-10] + "tampered123"
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        
        response = client.get('/api/user/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestAuthorizationSecurity:
    """Tests de sécurité pour les autorisations"""
    
    def test_organization_isolation(self):
        """Test isolation entre organisations"""
        # Créer deux organisations avec utilisateurs
        org1 = OrganizationFactory(name='Organization 1')
        org2 = OrganizationFactory(name='Organization 2')
        
        user1 = UserFactory()
        user2 = UserFactory()
        
        user1.organizations.add(org1)
        user2.organizations.add(org2)
        
        # Créer pipelines dans chaque org
        pipeline_org1 = PipelineFactory(organization=org1)
        pipeline_org2 = PipelineFactory(organization=org2)
        
        # Tester que user1 ne peut pas accéder aux pipelines de org2
        client = APIClient()
        client.force_authenticate(user=user1)
        
        # Accès à son propre pipeline
        response = client.get(f'/api/pipelines/{pipeline_org1.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        # Pas d'accès au pipeline de l'autre org
        response = client.get(f'/api/pipelines/{pipeline_org2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_role_based_permissions(self):
        """Test permissions basées sur les rôles"""
        from django.contrib.auth.models import Permission
        
        org = OrganizationFactory()
        
        # Utilisateur avec permission limitée
        viewer = UserFactory()
        viewer.organizations.add(org)
        
        # Utilisateur avec permissions complètes
        admin = UserFactory()
        admin.organizations.add(org)
        admin.user_permissions.add(
            Permission.objects.get(codename='add_pipeline'),
            Permission.objects.get(codename='change_pipeline'),
            Permission.objects.get(codename='delete_pipeline')
        )
        
        pipeline = PipelineFactory(organization=org)
        
        client = APIClient()
        
        # Test viewer: lecture seule
        client.force_authenticate(user=viewer)
        
        response = client.get(f'/api/pipelines/{pipeline.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        response = client.delete(f'/api/pipelines/{pipeline.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test admin: accès complet
        client.force_authenticate(user=admin)
        
        response = client.delete(f'/api/pipelines/{pipeline.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_api_rate_limiting(self):
        """Test limitation de taux des API"""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Faire de nombreuses requêtes rapidement
        responses = []
        for i in range(100):
            response = client.get('/api/pipelines/')
            responses.append(response.status_code)
        
        # Vérifier qu'au moins quelques requêtes sont limitées
        rate_limited_count = responses.count(status.HTTP_429_TOO_MANY_REQUESTS)
        assert rate_limited_count > 0, "Rate limiting should be triggered"
```

## Configuration d'intégration continue

### GitHub Actions workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_etl_platform
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/test.txt
    
    - name: Run linting
      run: |
        flake8 apps/ tests/
        black --check apps/ tests/
        isort --check-only apps/ tests/
    
    - name: Run security checks
      run: |
        bandit -r apps/
        safety check
    
    - name: Run unit tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_etl_platform
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/unit/ -v --cov=apps --cov-report=xml
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_etl_platform
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/integration/ -v
    
    - name: Run performance tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_etl_platform
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/performance/ -v -m "not memory"
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

Cette stratégie de test complète assure la qualité, la sécurité et les performances de la plateforme ETL à tous les niveaux.
