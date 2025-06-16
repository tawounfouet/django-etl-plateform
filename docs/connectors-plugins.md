# Connecteurs et Plugins - Django ETL Platform

## Architecture des connecteurs

### Design Pattern - Plugin Architecture

La plateforme utilise une architecture de plugins extensible permettant d'ajouter facilement de nouveaux connecteurs sans modifier le code core.

```python
# connectors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass
import pandas as pd

@dataclass
class ConnectionConfig:
    """Configuration standard pour tous les connecteurs"""
    connector_type: str
    name: str
    config: Dict[str, Any]
    credentials: Dict[str, Any]
    timeout: int = 30
    retry_count: int = 3

@dataclass
class SchemaInfo:
    """Information sur le schéma de données"""
    tables: List[str]
    columns: Dict[str, List[str]]
    data_types: Dict[str, Dict[str, str]]
    constraints: Dict[str, Any]

class BaseConnector(ABC):
    """Classe de base pour tous les connecteurs"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection = None
        
    @abstractmethod
    def test_connection(self) -> bool:
        """Teste la connectivité"""
        pass
    
    @abstractmethod
    def get_schema(self) -> SchemaInfo:
        """Récupère le schéma de la source"""
        pass
    
    @abstractmethod
    def extract(self, query: str, **kwargs) -> pd.DataFrame:
        """Extrait les données"""
        pass
    
    @abstractmethod
    def load(self, data: pd.DataFrame, destination: str, **kwargs) -> bool:
        """Charge les données"""
        pass
    
    @abstractmethod
    def get_preview(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Aperçu des données"""
        pass
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self):
        """Établit la connexion"""
        pass
    
    def disconnect(self):
        """Ferme la connexion"""
        if self.connection:
            self.connection.close()
            self.connection = None
```

### Registry Pattern pour les connecteurs

```python
# connectors/registry.py
from typing import Dict, Type, Optional
from .base import BaseConnector

class ConnectorRegistry:
    """Registry pour enregistrer et créer des connecteurs"""
    
    _connectors: Dict[str, Type[BaseConnector]] = {}
    
    @classmethod
    def register(cls, connector_type: str):
        """Decorator pour enregistrer un connecteur"""
        def decorator(connector_class: Type[BaseConnector]):
            cls._connectors[connector_type] = connector_class
            return connector_class
        return decorator
    
    @classmethod
    def create(cls, connector_type: str, config: ConnectionConfig) -> BaseConnector:
        """Crée une instance de connecteur"""
        if connector_type not in cls._connectors:
            raise ValueError(f"Unknown connector type: {connector_type}")
        
        connector_class = cls._connectors[connector_type]
        return connector_class(config)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Retourne les types de connecteurs disponibles"""
        return list(cls._connectors.keys())
    
    @classmethod
    def get_connector_info(cls, connector_type: str) -> Dict[str, Any]:
        """Retourne les informations sur un connecteur"""
        if connector_type not in cls._connectors:
            raise ValueError(f"Unknown connector type: {connector_type}")
        
        connector_class = cls._connectors[connector_type]
        return {
            'name': connector_class.__name__,
            'description': connector_class.__doc__,
            'config_schema': getattr(connector_class, 'CONFIG_SCHEMA', {}),
            'supported_operations': getattr(connector_class, 'SUPPORTED_OPERATIONS', [])
        }

# Usage
registry = ConnectorRegistry()

@registry.register('postgresql')
class PostgreSQLConnector(BaseConnector):
    """Connecteur PostgreSQL avec support des fonctionnalités avancées"""
    pass
```

## Connecteurs de base de données

### PostgreSQL Connector

```python
# connectors/database/postgresql.py
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
import pandas as pd
from typing import Optional, Iterator
import logging

@registry.register('postgresql')
class PostgreSQLConnector(BaseConnector):
    """Connecteur PostgreSQL optimisé pour les opérations ETL"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "host": {"type": "string"},
            "port": {"type": "integer", "default": 5432},
            "database": {"type": "string"},
            "schema": {"type": "string", "default": "public"},
            "ssl_mode": {"type": "string", "default": "prefer"},
            "application_name": {"type": "string", "default": "etl-platform"}
        },
        "required": ["host", "database"]
    }
    
    SUPPORTED_OPERATIONS = ['extract', 'load', 'upsert', 'schema_discovery']
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.connection_pool: Optional[ThreadedConnectionPool] = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Crée un pool de connexions"""
        try:
            conn_params = {
                'host': self.config.config['host'],
                'port': self.config.config.get('port', 5432),
                'database': self.config.config['database'],
                'user': self.config.credentials['username'],
                'password': self.config.credentials['password'],
                'sslmode': self.config.config.get('ssl_mode', 'prefer'),
                'application_name': self.config.config.get('application_name', 'etl-platform'),
                'connect_timeout': self.config.timeout
            }
            
            # Pool de connexions pour performance
            self.connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **conn_params
            )
            
            self.logger.info(f"Connected to PostgreSQL: {self.config.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def get_connection(self):
        """Récupère une connexion du pool"""
        if not self.connection_pool:
            self.connect()
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Retourne une connexion au pool"""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def test_connection(self) -> bool:
        """Teste la connexion à PostgreSQL"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.return_connection(conn)
            return result[0] == 1
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_schema(self) -> SchemaInfo:
        """Récupère le schéma de la base de données"""
        conn = self.get_connection()
        try:
            schema_name = self.config.config.get('schema', 'public')
            
            # Récupérer les tables
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            
            with conn.cursor() as cursor:
                cursor.execute(tables_query, (schema_name,))
                tables = [row[0] for row in cursor.fetchall()]
            
            # Récupérer les colonnes et types
            columns = {}
            data_types = {}
            
            for table in tables:
                columns_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(columns_query, (schema_name, table))
                    table_columns = cursor.fetchall()
                
                columns[table] = [col[0] for col in table_columns]
                data_types[table] = {
                    col[0]: {
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'default': col[3]
                    } for col in table_columns
                }
            
            return SchemaInfo(
                tables=tables,
                columns=columns,
                data_types=data_types,
                constraints={}  # TODO: Implement constraints discovery
            )
            
        finally:
            self.return_connection(conn)
    
    def extract(self, query: str, chunk_size: int = 10000, **kwargs) -> Iterator[pd.DataFrame]:
        """Extrait les données avec support du streaming"""
        conn = self.get_connection()
        try:
            # Utiliser un cursor server-side pour les gros volumes
            with conn.cursor(name='extract_cursor') as cursor:
                cursor.itersize = chunk_size
                cursor.execute(query)
                
                while True:
                    rows = cursor.fetchmany(chunk_size)
                    if not rows:
                        break
                    
                    # Récupérer les noms de colonnes
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Créer DataFrame
                    df = pd.DataFrame(rows, columns=columns)
                    yield df
                    
        except Exception as e:
            self.logger.error(f"Extract failed: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def load(self, data: pd.DataFrame, destination: str, mode: str = 'append', **kwargs) -> bool:
        """Charge les données dans PostgreSQL"""
        conn = self.get_connection()
        try:
            schema_name = self.config.config.get('schema', 'public')
            full_table_name = f"{schema_name}.{destination}"
            
            if mode == 'replace':
                # Supprimer et recréer la table
                self._create_table_from_dataframe(conn, data, full_table_name)
            elif mode == 'upsert' and 'upsert_key' in kwargs:
                # Upsert basé sur une clé
                return self._upsert_data(conn, data, full_table_name, kwargs['upsert_key'])
            
            # Insertion en batch pour performance
            self._bulk_insert(conn, data, full_table_name)
            conn.commit()
            
            self.logger.info(f"Loaded {len(data)} rows to {full_table_name}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Load failed: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def _bulk_insert(self, conn, data: pd.DataFrame, table_name: str):
        """Insertion en batch optimisée"""
        # Remplacer NaN par None pour PostgreSQL
        data_clean = data.where(pd.notnull(data), None)
        
        # Préparer les données pour COPY
        csv_buffer = io.StringIO()
        data_clean.to_csv(csv_buffer, index=False, header=False, sep='\t', na_rep='\\N')
        csv_buffer.seek(0)
        
        with conn.cursor() as cursor:
            # Utiliser COPY pour performance optimale
            columns = ', '.join(data.columns)
            copy_sql = f"COPY {table_name} ({columns}) FROM STDIN WITH (FORMAT CSV, DELIMITER '\t', NULL '\\N')"
            cursor.copy_expert(copy_sql, csv_buffer)
    
    def _upsert_data(self, conn, data: pd.DataFrame, table_name: str, upsert_key: str) -> bool:
        """Effectue un upsert basé sur une clé"""
        temp_table = f"{table_name}_temp_{int(time.time())}"
        
        try:
            # Créer table temporaire
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name})")
            
            # Charger dans table temporaire
            self._bulk_insert(conn, data, temp_table)
            
            # Effectuer l'upsert
            columns = list(data.columns)
            columns_str = ', '.join(columns)
            update_columns = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != upsert_key])
            
            upsert_sql = f"""
                INSERT INTO {table_name} ({columns_str})
                SELECT {columns_str} FROM {temp_table}
                ON CONFLICT ({upsert_key}) DO UPDATE SET {update_columns}
            """
            
            with conn.cursor() as cursor:
                cursor.execute(upsert_sql)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Upsert failed: {e}")
            raise
    
    def get_preview(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Aperçu des données avec limite"""
        # Ajouter LIMIT si pas déjà présent
        if 'LIMIT' not in query.upper():
            query = f"{query} LIMIT {limit}"
        
        # Utiliser next() pour récupérer le premier chunk seulement
        return next(self.extract(query, chunk_size=limit))
    
    def disconnect(self):
        """Ferme le pool de connexions"""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.connection_pool = None
            self.logger.info("Disconnected from PostgreSQL")
```

### MySQL Connector

```python
# connectors/database/mysql.py
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
import pandas as pd

@registry.register('mysql')
class MySQLConnector(BaseConnector):
    """Connecteur MySQL optimisé"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "host": {"type": "string"},
            "port": {"type": "integer", "default": 3306},
            "database": {"type": "string"},
            "charset": {"type": "string", "default": "utf8mb4"},
            "use_ssl": {"type": "boolean", "default": True}
        },
        "required": ["host", "database"]
    }
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool_config = {
            'pool_name': f'pool_{self.config.name}',
            'pool_size': 5,
            'pool_reset_session': True,
            'host': self.config.config['host'],
            'port': self.config.config.get('port', 3306),
            'database': self.config.config['database'],
            'user': self.config.credentials['username'],
            'password': self.config.credentials['password'],
            'charset': self.config.config.get('charset', 'utf8mb4'),
            'use_ssl': self.config.config.get('use_ssl', True),
            'connect_timeout': self.config.timeout
        }
    
    def connect(self):
        """Crée le pool de connexions MySQL"""
        try:
            self.connection_pool = MySQLConnectionPool(**self.pool_config)
            self.logger.info(f"Connected to MySQL: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Teste la connexion MySQL"""
        try:
            conn = self.connection_pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] == 1
        except Exception as e:
            self.logger.error(f"MySQL connection test failed: {e}")
            return False
    
    def extract(self, query: str, chunk_size: int = 10000, **kwargs) -> Iterator[pd.DataFrame]:
        """Extraction avec streaming pour MySQL"""
        conn = self.connection_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
                yield df
                
        finally:
            cursor.close()
            conn.close()
    
    def load(self, data: pd.DataFrame, destination: str, **kwargs) -> bool:
        """Chargement optimisé pour MySQL"""
        conn = self.connection_pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # Utiliser INSERT ... VALUES pour MySQL
            columns = ', '.join(data.columns)
            placeholders = ', '.join(['%s'] * len(data.columns))
            insert_sql = f"INSERT INTO {destination} ({columns}) VALUES ({placeholders})"
            
            # Convertir DataFrame en liste de tuples
            data_tuples = [tuple(row) for row in data.to_numpy()]
            
            # Insertion en batch
            cursor.executemany(insert_sql, data_tuples)
            conn.commit()
            
            self.logger.info(f"Loaded {len(data)} rows to {destination}")
            return True
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"MySQL load failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
```

## Connecteurs API

### REST API Connector

```python
# connectors/api/rest.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from typing import Dict, Any, Optional, Iterator
import json
import time

@registry.register('rest_api')
class RESTAPIConnector(BaseConnector):
    """Connecteur REST API avec gestion des limites de taux et pagination"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "base_url": {"type": "string"},
            "auth_type": {"type": "string", "enum": ["none", "basic", "bearer", "api_key", "oauth2"]},
            "headers": {"type": "object"},
            "timeout": {"type": "integer", "default": 30},
            "rate_limit": {"type": "integer", "default": 100},  # requests per minute
            "pagination_type": {"type": "string", "enum": ["offset", "cursor", "page"]},
            "max_retries": {"type": "integer", "default": 3}
        },
        "required": ["base_url"]
    }
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.session = None
        self.last_request_time = 0
        self.rate_limit = self.config.config.get('rate_limit', 100)  # per minute
        self.min_interval = 60 / self.rate_limit  # seconds between requests
    
    def connect(self):
        """Initialise la session HTTP avec retry strategy"""
        self.session = requests.Session()
        
        # Configuration des retries
        retry_strategy = Retry(
            total=self.config.config.get('max_retries', 3),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configuration de l'authentification
        self._setup_authentication()
        
        # Headers par défaut
        default_headers = {
            'User-Agent': 'ETL-Platform/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        default_headers.update(self.config.config.get('headers', {}))
        self.session.headers.update(default_headers)
    
    def _setup_authentication(self):
        """Configure l'authentification selon le type"""
        auth_type = self.config.config.get('auth_type', 'none')
        
        if auth_type == 'basic':
            self.session.auth = (
                self.config.credentials['username'],
                self.config.credentials['password']
            )
        elif auth_type == 'bearer':
            self.session.headers['Authorization'] = f"Bearer {self.config.credentials['token']}"
        elif auth_type == 'api_key':
            key_name = self.config.config.get('api_key_header', 'X-API-Key')
            self.session.headers[key_name] = self.config.credentials['api_key']
        elif auth_type == 'oauth2':
            # Implémentation OAuth2 (refresh token, etc.)
            self._setup_oauth2()
    
    def _setup_oauth2(self):
        """Configuration OAuth2 avec gestion du refresh token"""
        # TODO: Implémenter OAuth2 flow complet
        pass
    
    def _rate_limit_wait(self):
        """Respecte les limites de taux"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def test_connection(self) -> bool:
        """Teste la connexion à l'API"""
        try:
            if not self.session:
                self.connect()
            
            # Test avec endpoint de health check ou base URL
            test_url = self.config.config.get('health_check_endpoint', '')
            if not test_url:
                test_url = self.config.config['base_url']
            
            self._rate_limit_wait()
            response = self.session.head(test_url, timeout=self.config.timeout)
            
            return response.status_code < 400
            
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return False
    
    def extract(self, endpoint: str, params: Dict[str, Any] = None, **kwargs) -> Iterator[pd.DataFrame]:
        """Extraction avec pagination automatique"""
        if not self.session:
            self.connect()
        
        base_url = self.config.config['base_url'].rstrip('/')
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        if params is None:
            params = {}
        
        pagination_type = self.config.config.get('pagination_type', 'offset')
        
        if pagination_type == 'offset':
            yield from self._extract_with_offset_pagination(url, params, **kwargs)
        elif pagination_type == 'cursor':
            yield from self._extract_with_cursor_pagination(url, params, **kwargs)
        elif pagination_type == 'page':
            yield from self._extract_with_page_pagination(url, params, **kwargs)
        else:
            # Pas de pagination
            yield from self._extract_single_request(url, params, **kwargs)
    
    def _extract_with_offset_pagination(self, url: str, params: Dict, **kwargs) -> Iterator[pd.DataFrame]:
        """Pagination par offset/limit"""
        offset = 0
        limit = kwargs.get('page_size', 100)
        
        while True:
            current_params = params.copy()
            current_params.update({
                'offset': offset,
                'limit': limit
            })
            
            self._rate_limit_wait()
            response = self.session.get(url, params=current_params, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Extraire les résultats selon la structure de l'API
            results = self._extract_results_from_response(data)
            
            if not results:
                break
            
            df = pd.DataFrame(results)
            yield df
            
            # Vérifier s'il y a plus de données
            if len(results) < limit:
                break
            
            offset += limit
    
    def _extract_with_cursor_pagination(self, url: str, params: Dict, **kwargs) -> Iterator[pd.DataFrame]:
        """Pagination par curseur"""
        cursor = None
        
        while True:
            current_params = params.copy()
            if cursor:
                current_params['cursor'] = cursor
            
            self._rate_limit_wait()
            response = self.session.get(url, params=current_params, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = self._extract_results_from_response(data)
            
            if not results:
                break
            
            df = pd.DataFrame(results)
            yield df
            
            # Récupérer le prochain curseur
            cursor = data.get('next_cursor') or data.get('pagination', {}).get('next_cursor')
            if not cursor:
                break
    
    def _extract_results_from_response(self, data: Dict[str, Any]) -> List[Dict]:
        """Extrait les résultats de la réponse selon différents formats"""
        # Essayer différents formats de réponse API
        if isinstance(data, list):
            return data
        elif 'data' in data:
            return data['data']
        elif 'results' in data:
            return data['results']
        elif 'items' in data:
            return data['items']
        else:
            # Si la structure n'est pas reconnue, retourner la réponse complète
            return [data]
    
    def load(self, data: pd.DataFrame, endpoint: str, method: str = 'POST', **kwargs) -> bool:
        """Chargement de données via API"""
        if not self.session:
            self.connect()
        
        base_url = self.config.config['base_url'].rstrip('/')
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # Convertir DataFrame en format JSON
        records = data.to_dict('records')
        
        batch_size = kwargs.get('batch_size', 100)
        
        try:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                self._rate_limit_wait()
                
                if method.upper() == 'POST':
                    response = self.session.post(url, json=batch, timeout=self.config.timeout)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=batch, timeout=self.config.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                self.logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} records")
            
            return True
            
        except Exception as e:
            self.logger.error(f"API load failed: {e}")
            raise
    
    def get_schema(self) -> SchemaInfo:
        """Récupère le schéma de l'API (endpoints disponibles)"""
        # Essayer de récupérer la documentation OpenAPI/Swagger
        try:
            swagger_url = f"{self.config.config['base_url']}/swagger.json"
            response = self.session.get(swagger_url)
            
            if response.status_code == 200:
                swagger_doc = response.json()
                return self._parse_swagger_schema(swagger_doc)
        except:
            pass
        
        # Fallback: retourner schéma basique
        return SchemaInfo(
            tables=['api_endpoints'],
            columns={'api_endpoints': ['endpoint', 'method', 'description']},
            data_types={'api_endpoints': {
                'endpoint': {'type': 'string'},
                'method': {'type': 'string'},
                'description': {'type': 'string'}
            }},
            constraints={}
        )
```

## Connecteurs Cloud

### S3 Connector

```python
# connectors/cloud/s3.py
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
from typing import Iterator, List
import io
import os

@registry.register('s3')
class S3Connector(BaseConnector):
    """Connecteur Amazon S3 avec support multi-format"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "bucket": {"type": "string"},
            "region": {"type": "string", "default": "us-east-1"},
            "prefix": {"type": "string", "default": ""},
            "endpoint_url": {"type": "string"},  # Pour S3-compatible (MinIO, etc.)
            "use_ssl": {"type": "boolean", "default": True}
        },
        "required": ["bucket"]
    }
    
    SUPPORTED_FORMATS = ['csv', 'json', 'parquet', 'xlsx']
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.s3_client = None
        self.bucket = self.config.config['bucket']
    
    def connect(self):
        """Initialise le client S3"""
        try:
            session_config = {
                'region_name': self.config.config.get('region', 'us-east-1'),
                'aws_access_key_id': self.config.credentials.get('access_key_id'),
                'aws_secret_access_key': self.config.credentials.get('secret_access_key'),
            }
            
            # Support pour S3-compatible endpoints
            if 'endpoint_url' in self.config.config:
                session_config['endpoint_url'] = self.config.config['endpoint_url']
                session_config['use_ssl'] = self.config.config.get('use_ssl', True)
            
            # Support pour AWS SSO/role-based auth
            if 'role_arn' in self.config.credentials:
                session = boto3.Session()
                sts_client = session.client('sts')
                response = sts_client.assume_role(
                    RoleArn=self.config.credentials['role_arn'],
                    RoleSessionName='etl-platform-session'
                )
                credentials = response['Credentials']
                session_config.update({
                    'aws_access_key_id': credentials['AccessKeyId'],
                    'aws_secret_access_key': credentials['SecretAccessKey'],
                    'aws_session_token': credentials['SessionToken']
                })
            
            self.s3_client = boto3.client('s3', **session_config)
            self.logger.info(f"Connected to S3 bucket: {self.bucket}")
            
        except (ClientError, NoCredentialsError) as e:
            self.logger.error(f"Failed to connect to S3: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Teste l'accès au bucket S3"""
        try:
            if not self.s3_client:
                self.connect()
            
            # Tester l'accès au bucket
            self.s3_client.head_bucket(Bucket=self.bucket)
            return True
            
        except ClientError as e:
            self.logger.error(f"S3 connection test failed: {e}")
            return False
    
    def list_files(self, prefix: str = "", file_extension: str = None) -> List[str]:
        """Liste les fichiers dans le bucket"""
        if not self.s3_client:
            self.connect()
        
        full_prefix = self.config.config.get('prefix', '') + prefix
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=full_prefix)
            
            files = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        file_key = obj['Key']
                        if file_extension and not file_key.endswith(file_extension):
                            continue
                        files.append(file_key)
            
            return files
            
        except ClientError as e:
            self.logger.error(f"Failed to list S3 files: {e}")
            raise
    
    def extract(self, file_path: str, file_format: str = None, **kwargs) -> Iterator[pd.DataFrame]:
        """Extraction de fichiers S3 avec auto-détection du format"""
        if not self.s3_client:
            self.connect()
        
        # Auto-détection du format si non spécifié
        if not file_format:
            file_format = self._detect_file_format(file_path)
        
        try:
            # Télécharger le fichier en mémoire
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            file_content = response['Body'].read()
            
            # Parser selon le format
            if file_format == 'csv':
                df = pd.read_csv(io.BytesIO(file_content), **kwargs)
            elif file_format == 'json':
                df = pd.read_json(io.BytesIO(file_content), **kwargs)
            elif file_format == 'parquet':
                df = pd.read_parquet(io.BytesIO(file_content), **kwargs)
            elif file_format == 'xlsx':
                df = pd.read_excel(io.BytesIO(file_content), **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            # Retourner par chunks si le fichier est gros
            chunk_size = kwargs.get('chunk_size', 10000)
            if len(df) > chunk_size:
                for i in range(0, len(df), chunk_size):
                    yield df[i:i + chunk_size]
            else:
                yield df
                
        except ClientError as e:
            self.logger.error(f"Failed to extract from S3 file {file_path}: {e}")
            raise
    
    def load(self, data: pd.DataFrame, file_path: str, file_format: str = 'csv', **kwargs) -> bool:
        """Chargement de données vers S3"""
        if not self.s3_client:
            self.connect()
        
        try:
            # Convertir DataFrame selon le format
            buffer = io.BytesIO()
            
            if file_format == 'csv':
                data.to_csv(buffer, index=False, **kwargs)
            elif file_format == 'json':
                data.to_json(buffer, orient='records', **kwargs)
            elif file_format == 'parquet':
                data.to_parquet(buffer, index=False, **kwargs)
            elif file_format == 'xlsx':
                data.to_excel(buffer, index=False, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            buffer.seek(0)
            
            # Upload vers S3
            full_path = self.config.config.get('prefix', '') + file_path
            self.s3_client.upload_fileobj(
                buffer, 
                self.bucket, 
                full_path,
                ExtraArgs=kwargs.get('extra_args', {})
            )
            
            self.logger.info(f"Loaded {len(data)} rows to s3://{self.bucket}/{full_path}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to load to S3: {e}")
            raise
    
    def _detect_file_format(self, file_path: str) -> str:
        """Détecte le format de fichier basé sur l'extension"""
        extension = file_path.split('.')[-1].lower()
        format_mapping = {
            'csv': 'csv',
            'json': 'json',
            'jsonl': 'json',
            'parquet': 'parquet',
            'xlsx': 'xlsx',
            'xls': 'xlsx'
        }
        return format_mapping.get(extension, 'csv')
    
    def get_schema(self) -> SchemaInfo:
        """Récupère la structure des fichiers dans le bucket"""
        files = self.list_files()
        
        # Grouper par format
        file_types = {}
        for file_path in files[:100]:  # Limiter pour performance
            file_format = self._detect_file_format(file_path)
            if file_format not in file_types:
                file_types[file_format] = []
            file_types[file_format].append(file_path)
        
        return SchemaInfo(
            tables=list(file_types.keys()),
            columns={fmt: ['file_path', 'size', 'modified'] for fmt in file_types.keys()},
            data_types={fmt: {
                'file_path': {'type': 'string'},
                'size': {'type': 'integer'},
                'modified': {'type': 'datetime'}
            } for fmt in file_types.keys()},
            constraints={}
        )
```

## Plugin Development Kit

### Interface pour développeurs externes

```python
# connectors/plugin_sdk.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

class ConnectorPlugin(ABC):
    """Interface pour les plugins de connecteurs développés par des tiers"""
    
    # Métadonnées obligatoires
    PLUGIN_NAME: str = None
    PLUGIN_VERSION: str = None
    PLUGIN_AUTHOR: str = None
    PLUGIN_DESCRIPTION: str = None
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Retourne le schéma JSON de configuration"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valide la configuration"""
        pass
    
    @abstractmethod
    def create_connector(self, config: ConnectionConfig) -> BaseConnector:
        """Crée une instance du connecteur"""
        pass
    
    def get_supported_operations(self) -> List[str]:
        """Retourne les opérations supportées"""
        return ['extract', 'load']
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Retourne les informations du plugin"""
        return {
            'name': self.PLUGIN_NAME,
            'version': self.PLUGIN_VERSION,
            'author': self.PLUGIN_AUTHOR,
            'description': self.PLUGIN_DESCRIPTION,
            'supported_operations': self.get_supported_operations()
        }

# Exemple d'implémentation pour Salesforce
class SalesforcePlugin(ConnectorPlugin):
    PLUGIN_NAME = "Salesforce Connector"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_AUTHOR = "ETL Platform Team"
    PLUGIN_DESCRIPTION = "Connecteur pour Salesforce CRM"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "instance_url": {"type": "string"},
                "api_version": {"type": "string", "default": "v54.0"},
                "sandbox": {"type": "boolean", "default": False}
            },
            "required": ["instance_url"]
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        # Validation personnalisée
        return 'instance_url' in config
    
    def create_connector(self, config: ConnectionConfig) -> BaseConnector:
        return SalesforceConnector(config)

# Gestionnaire de plugins
class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, ConnectorPlugin] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_plugin(self, plugin: ConnectorPlugin):
        """Enregistre un plugin"""
        if not plugin.PLUGIN_NAME:
            raise ValueError("Plugin must have a PLUGIN_NAME")
        
        self.plugins[plugin.PLUGIN_NAME] = plugin
        
        # Enregistrer le connecteur dans le registry principal
        connector_type = plugin.PLUGIN_NAME.lower().replace(' ', '_')
        
        def plugin_factory(config: ConnectionConfig) -> BaseConnector:
            return plugin.create_connector(config)
        
        ConnectorRegistry._connectors[connector_type] = plugin_factory
        
        self.logger.info(f"Registered plugin: {plugin.PLUGIN_NAME} v{plugin.PLUGIN_VERSION}")
    
    def load_plugins_from_directory(self, plugin_dir: str):
        """Charge automatiquement les plugins depuis un répertoire"""
        import importlib.util
        import os
        
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                file_path = os.path.join(plugin_dir, filename)
                spec = importlib.util.spec_from_file_location(filename[:-3], file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Chercher les classes de plugin
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, ConnectorPlugin) and 
                        attr != ConnectorPlugin):
                        
                        plugin_instance = attr()
                        self.register_plugin(plugin_instance)
    
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Retourne la liste des plugins disponibles"""
        return [plugin.get_plugin_info() for plugin in self.plugins.values()]

# Instance globale du gestionnaire de plugins
plugin_manager = PluginManager()
```

### Configuration et utilisation

```python
# management/commands/load_plugins.py
from django.core.management.base import BaseCommand
from connectors.plugin_sdk import plugin_manager
import os

class Command(BaseCommand):
    help = 'Load connector plugins from plugins directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plugin-dir',
            type=str,
            default='plugins/',
            help='Directory containing plugin files'
        )

    def handle(self, *args, **options):
        plugin_dir = options['plugin_dir']
        
        if not os.path.exists(plugin_dir):
            self.stdout.write(
                self.style.WARNING(f'Plugin directory {plugin_dir} does not exist')
            )
            return
        
        plugin_manager.load_plugins_from_directory(plugin_dir)
        
        plugins = plugin_manager.get_available_plugins()
        self.stdout.write(
            self.style.SUCCESS(f'Loaded {len(plugins)} plugins:')
        )
        
        for plugin in plugins:
            self.stdout.write(f"  - {plugin['name']} v{plugin['version']}")
```

Cette architecture de connecteurs et plugins offre une base solide et extensible pour la plateforme ETL, permettant une intégration facile avec de nombreuses sources de données tout en maintenant la cohérence et la performance.
