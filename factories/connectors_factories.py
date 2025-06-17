"""
Factories pour les modèles de connecteurs
"""
import factory
import json
from cryptography.fernet import Fernet
from faker import Faker
from apps.connectors.models import (
    Credential, Connector, DatabaseConnector, 
    APIConnector, FileConnector, CloudConnector,
    ConnectorType
)
from .core_factories import OrganizationFactory
from .authentication_factories import CustomUserFactory

fake = Faker('fr_FR')


class CredentialFactory(factory.django.DjangoModelFactory):
    """Factory pour Credential"""
    
    class Meta:
        model = Credential

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    organization = factory.SubFactory(OrganizationFactory)
    encryption_key_id = factory.Faker('uuid4')
    expires_at = factory.Faker('future_datetime', end_date='+1y')
    
    @factory.lazy_attribute
    def encrypted_data(self):
        # Simuler des données d'authentification chiffrées
        data = {
            'username': fake.user_name(),
            'password': fake.password(),
            'api_key': fake.sha256(),
            'token': fake.sha1(),
        }
        # Pour les tests, on utilise une clé fixe
        key = Fernet.generate_key()
        fernet = Fernet(key)
        return fernet.encrypt(json.dumps(data).encode()).decode()


class ConnectorFactory(factory.django.DjangoModelFactory):
    """Factory pour Connector"""
    
    class Meta:
        model = Connector

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    connector_type = factory.Faker('random_element', elements=[
        ConnectorType.DATABASE,
        ConnectorType.API,
        ConnectorType.FILE,
        ConnectorType.CLOUD,
    ])
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(CustomUserFactory)
    credential = factory.SubFactory(CredentialFactory)
    is_active = factory.Faker('boolean', chance_of_getting_true=85)
    
    config = factory.LazyFunction(lambda: {
        'description': fake.text(max_nb_chars=200),
        'tags': fake.words(nb=fake.random_int(1, 5)),
        'environment': fake.random_element(['dev', 'staging', 'prod']),
        'team': fake.random_element(['data', 'analytics', 'engineering']),
        'contact_email': fake.email(),
        'documentation_url': fake.url(),
        'maintenance_window': {
            'day': fake.random_element(['monday', 'tuesday', 'sunday']),
            'start_time': fake.time(),
            'duration_hours': fake.random_int(1, 4),
        }
    })


class DatabaseConnectorFactory(factory.django.DjangoModelFactory):
    """Factory pour DatabaseConnector"""
    
    class Meta:
        model = DatabaseConnector

    connector = factory.SubFactory(
        ConnectorFactory,
        connector_type=ConnectorType.DATABASE
    )
    
    database_type = factory.Faker('random_element', elements=[
        'postgresql', 'mysql', 'sqlite', 'oracle', 'sqlserver'
    ])
    host = factory.Faker('domain_name')
    port = factory.LazyAttribute(lambda obj: {
        'postgresql': 5432,
        'mysql': 3306,
        'sqlite': 0,
        'oracle': 1521,
        'sqlserver': 1433,
    }.get(obj.database_type, 5432))
    database_name = factory.Faker('word')
    schema_name = factory.Faker('word')
    ssl_enabled = factory.Faker('boolean', chance_of_getting_true=70)
    connection_timeout = factory.Faker('random_int', min=10, max=120)


class APIConnectorFactory(factory.django.DjangoModelFactory):
    """Factory pour APIConnector"""
    
    class Meta:
        model = APIConnector

    connector = factory.SubFactory(
        ConnectorFactory,
        connector_type=ConnectorType.API
    )
    
    base_url = factory.Faker('url')
    auth_type = factory.Faker('random_element', elements=[
        'none', 'basic', 'bearer', 'oauth2', 'api_key'
    ])
    timeout = factory.Faker('random_int', min=10, max=300)
    retry_count = factory.Faker('random_int', min=1, max=5)
    rate_limit = factory.Faker('random_int', min=100, max=10000)
    
    headers = factory.LazyFunction(lambda: {
        'User-Agent': fake.user_agent(),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-Version': fake.random_element(['v1', 'v2', 'v3']),
        'X-Client-Id': fake.uuid4(),
    })


class FileConnectorFactory(factory.django.DjangoModelFactory):
    """Factory pour FileConnector"""
    
    class Meta:
        model = FileConnector

    connector = factory.SubFactory(
        ConnectorFactory,
        connector_type=ConnectorType.FILE
    )
    
    file_type = factory.Faker('random_element', elements=[
        'csv', 'json', 'xml', 'excel', 'parquet'
    ])
    file_path = factory.Faker('file_path', depth=3, extension='csv')
    encoding = factory.Faker('random_element', elements=[
        'utf-8', 'latin-1', 'ascii', 'utf-16'
    ])
    delimiter = factory.LazyAttribute(lambda obj: {
        'csv': ',',
        'tsv': '\t',
        'pipe': '|',
    }.get(obj.file_type, ','))
    has_header = factory.Faker('boolean', chance_of_getting_true=80)
    quote_char = factory.Faker('random_element', elements=['"', "'", '`'])


class CloudConnectorFactory(factory.django.DjangoModelFactory):
    """Factory pour CloudConnector"""
    
    class Meta:
        model = CloudConnector

    connector = factory.SubFactory(
        ConnectorFactory,
        connector_type=ConnectorType.CLOUD
    )
    
    provider = factory.Faker('random_element', elements=[
        'aws_s3', 'azure_blob', 'gcp_storage', 'minio'
    ])
    bucket_name = factory.Faker('slug')
    region = factory.LazyAttribute(lambda obj: {
        'aws_s3': fake.random_element(['us-east-1', 'eu-west-1', 'ap-southeast-1']),
        'azure_blob': fake.random_element(['eastus', 'westeurope', 'southeastasia']),
        'gcp_storage': fake.random_element(['us-central1', 'europe-west1', 'asia-east1']),
        'minio': 'local',
    }.get(obj.provider, 'us-east-1'))
    endpoint_url = factory.LazyAttribute(lambda obj: {
        'minio': f'http://{fake.domain_name()}:9000',
        'aws_s3': '',
        'azure_blob': f'https://{fake.word()}.blob.core.windows.net',
        'gcp_storage': '',
    }.get(obj.provider, ''))


# Factories spécialisées pour des connecteurs réalistes

class PostgreSQLConnectorFactory(DatabaseConnectorFactory):
    """Factory pour connecteur PostgreSQL"""
    database_type = 'postgresql'
    port = 5432
    ssl_enabled = True


class MySQLConnectorFactory(DatabaseConnectorFactory):
    """Factory pour connecteur MySQL"""
    database_type = 'mysql'
    port = 3306
    ssl_enabled = True


class RESTAPIConnectorFactory(APIConnectorFactory):
    """Factory pour API REST"""
    auth_type = 'bearer'
    base_url = factory.LazyAttribute(
        lambda obj: f'https://api.{fake.domain_name()}/v1'
    )
    headers = factory.LazyFunction(lambda: {
        'User-Agent': 'ETL-Platform/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    })


class CSVFileConnectorFactory(FileConnectorFactory):
    """Factory pour fichiers CSV"""
    file_type = 'csv'
    delimiter = ','
    has_header = True
    encoding = 'utf-8'


class S3ConnectorFactory(CloudConnectorFactory):
    """Factory pour Amazon S3"""
    provider = 'aws_s3'
    region = 'us-east-1'
    endpoint_url = ''


class AzureBlobConnectorFactory(CloudConnectorFactory):
    """Factory pour Azure Blob Storage"""
    provider = 'azure_blob'
    region = 'eastus'
    endpoint_url = factory.LazyAttribute(
        lambda obj: f'https://{obj.bucket_name}.blob.core.windows.net'
    )


# Factory pour créer un ensemble complet de connecteurs

class ConnectorSetFactory(factory.django.DjangoModelFactory):
    """Factory qui crée un ensemble de connecteurs pour une organisation"""
    
    class Meta:
        model = Connector

    @classmethod
    def create_complete_set(cls, organization=None, created_by=None):
        """Crée un ensemble complet de connecteurs"""
        if not organization:
            organization = OrganizationFactory()
        if not created_by:
            created_by = CustomUserFactory()
        
        connectors = []
        
        # Base de données
        pg_connector = ConnectorFactory(
            name='Production PostgreSQL',
            connector_type=ConnectorType.DATABASE,
            organization=organization,
            created_by=created_by
        )
        PostgreSQLConnectorFactory(connector=pg_connector)
        connectors.append(pg_connector)
        
        mysql_connector = ConnectorFactory(
            name='Analytics MySQL',
            connector_type=ConnectorType.DATABASE,
            organization=organization,
            created_by=created_by
        )
        MySQLConnectorFactory(connector=mysql_connector)
        connectors.append(mysql_connector)
        
        # APIs
        crm_connector = ConnectorFactory(
            name='CRM API',
            connector_type=ConnectorType.API,
            organization=organization,
            created_by=created_by
        )
        RESTAPIConnectorFactory(connector=crm_connector)
        connectors.append(crm_connector)
        
        marketing_connector = ConnectorFactory(
            name='Marketing Platform API',
            connector_type=ConnectorType.API,
            organization=organization,
            created_by=created_by
        )
        RESTAPIConnectorFactory(connector=marketing_connector)
        connectors.append(marketing_connector)
        
        # Fichiers
        csv_connector = ConnectorFactory(
            name='Daily Reports CSV',
            connector_type=ConnectorType.FILE,
            organization=organization,
            created_by=created_by
        )
        CSVFileConnectorFactory(connector=csv_connector)
        connectors.append(csv_connector)
        
        # Cloud
        s3_connector = ConnectorFactory(
            name='Data Lake S3',
            connector_type=ConnectorType.CLOUD,
            organization=organization,
            created_by=created_by
        )
        S3ConnectorFactory(connector=s3_connector)
        connectors.append(s3_connector)
        
        return connectors
