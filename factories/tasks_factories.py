"""
Factories pour les modèles de tâches
"""
import factory
from faker import Faker
from apps.tasks.models import (
    TaskTemplate, Task, TaskParameter, TaskDependency,
    TaskType
)
from .core_factories import OrganizationFactory
from .authentication_factories import CustomUserFactory
from .pipelines_factories import PipelineStepFactory

fake = Faker('fr_FR')


class TaskTemplateFactory(factory.django.DjangoModelFactory):
    """Factory pour TaskTemplate"""
    
    class Meta:
        model = TaskTemplate

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=300)
    task_type = factory.Faker('random_element', elements=[
        TaskType.EXTRACT,
        TaskType.TRANSFORM,
        TaskType.LOAD,
        TaskType.VALIDATE,
        TaskType.NOTIFY,
        TaskType.CUSTOM,
    ])
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(CustomUserFactory)
    is_public = factory.Faker('boolean', chance_of_getting_true=30)
    version = factory.Faker('random_element', elements=[
        '1.0.0', '1.1.0', '1.2.0', '2.0.0'
    ])
    
    config_schema = factory.LazyAttribute(lambda obj: _generate_config_schema(obj.task_type))
    default_config = factory.LazyAttribute(lambda obj: _generate_default_config(obj.task_type))


def _generate_config_schema(task_type):
    """Génère un schéma JSON pour la configuration de la tâche"""
    base_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Nom de la tâche"
            },
            "description": {
                "type": "string",
                "description": "Description de la tâche"
            },
            "timeout_seconds": {
                "type": "integer",
                "minimum": 1,
                "maximum": 86400,
                "description": "Timeout en secondes"
            }
        },
        "required": ["name"]
    }
    
    if task_type == TaskType.EXTRACT:
        base_schema["properties"].update({
            "source_connection": {
                "type": "string",
                "description": "ID de la connexion source"
            },
            "query": {
                "type": "string",
                "description": "Requête ou chemin des données"
            },
            "batch_size": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000000
            }
        })
    elif task_type == TaskType.TRANSFORM:
        base_schema["properties"].update({
            "transformation_script": {
                "type": "string",
                "description": "Script de transformation"
            },
            "engine": {
                "type": "string",
                "enum": ["python", "sql", "spark"]
            }
        })
    elif task_type == TaskType.LOAD:
        base_schema["properties"].update({
            "target_connection": {
                "type": "string",
                "description": "ID de la connexion cible"
            },
            "target_table": {
                "type": "string",
                "description": "Table ou fichier cible"
            },
            "load_strategy": {
                "type": "string",
                "enum": ["insert", "upsert", "replace"]
            }
        })
    
    return base_schema


def _generate_default_config(task_type):
    """Génère une configuration par défaut pour la tâche"""
    base_config = {
        "timeout_seconds": 3600,
        "retry_count": 3,
        "retry_delay": 60
    }
    
    if task_type == TaskType.EXTRACT:
        base_config.update({
            "batch_size": 10000,
            "incremental": False,
            "parallel_workers": 1
        })
    elif task_type == TaskType.TRANSFORM:
        base_config.update({
            "engine": "python",
            "memory_limit_mb": 1024
        })
    elif task_type == TaskType.LOAD:
        base_config.update({
            "load_strategy": "insert",
            "batch_size": 5000,
            "create_indexes": True
        })
    
    return base_config


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory pour Task"""
    
    class Meta:
        model = Task

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    pipeline_step = factory.SubFactory(PipelineStepFactory)
    template = factory.SubFactory(TaskTemplateFactory)
    task_type = factory.LazyAttribute(lambda obj: obj.template.task_type if obj.template else TaskType.CUSTOM)
    order_index = factory.Sequence(lambda n: n)
    is_enabled = factory.Faker('boolean', chance_of_getting_true=90)
    retry_count = factory.Faker('random_int', min=0, max=5)
    timeout_seconds = factory.Faker('random_int', min=60, max=7200)
    
    config = factory.LazyAttribute(lambda obj: _generate_task_config(obj.task_type))


def _generate_task_config(task_type):
    """Génère une configuration spécifique pour la tâche"""
    base_config = {
        "description": fake.text(max_nb_chars=200),
        "environment": fake.random_element(['dev', 'staging', 'prod']),
        "monitoring": {
            "metrics_enabled": fake.boolean(),
            "logging_level": fake.random_element(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
            "alerts_enabled": fake.boolean()
        }
    }
    
    if task_type == TaskType.EXTRACT:
        base_config.update({
            "source": {
                "type": fake.random_element(['database', 'api', 'file']),
                "connection_id": fake.uuid4(),
                "query": fake.text(max_nb_chars=100),
                "incremental": fake.boolean(),
                "watermark_column": fake.random_element(['updated_at', 'created_at', 'id'])
            },
            "output": {
                "format": fake.random_element(['json', 'csv', 'parquet']),
                "compression": fake.random_element(['none', 'gzip', 'snappy']),
                "partitioning": fake.boolean()
            },
            "performance": {
                "batch_size": fake.random_int(1000, 100000),
                "parallel_workers": fake.random_int(1, 8),
                "memory_limit_mb": fake.random_int(512, 4096)
            }
        })
    elif task_type == TaskType.TRANSFORM:
        base_config.update({
            "transformation": {
                "engine": fake.random_element(['python', 'sql', 'spark']),
                "script": fake.text(max_nb_chars=200),
                "functions": fake.random_elements([
                    'clean_data', 'normalize', 'aggregate', 'join', 'pivot'
                ], length=fake.random_int(1, 3))
            },
            "validation": {
                "schema_check": fake.boolean(),
                "quality_rules": fake.random_elements([
                    'not_null', 'unique', 'range_check'
                ], length=fake.random_int(0, 3))
            }
        })
    elif task_type == TaskType.LOAD:
        base_config.update({
            "target": {
                "type": fake.random_element(['database', 'file', 'api']),
                "connection_id": fake.uuid4(),
                "table_name": fake.word(),
                "schema": fake.random_element(['public', 'analytics', 'staging'])
            },
            "loading": {
                "strategy": fake.random_element(['insert', 'upsert', 'replace']),
                "batch_size": fake.random_int(1000, 50000),
                "create_indexes": fake.boolean(),
                "vacuum_after": fake.boolean()
            }
        })
    elif task_type == TaskType.VALIDATE:
        base_config.update({
            "validation_rules": [
                {
                    "type": "not_null",
                    "columns": fake.words(nb=fake.random_int(1, 5))
                },
                {
                    "type": "unique",
                    "columns": fake.words(nb=fake.random_int(1, 3))
                },
                {
                    "type": "range_check",
                    "column": fake.word(),
                    "min_value": fake.random_int(0, 100),
                    "max_value": fake.random_int(101, 1000)
                }
            ],
            "error_handling": {
                "tolerance_threshold": fake.random_int(0, 10),
                "action_on_failure": fake.random_element(['stop', 'warn', 'quarantine'])
            }
        })
    elif task_type == TaskType.NOTIFY:
        base_config.update({
            "notification": {
                "channels": fake.random_elements(['email', 'slack', 'webhook'], length=2),
                "recipients": [fake.email() for _ in range(fake.random_int(1, 3))],
                "template": fake.random_element(['success', 'failure', 'warning']),
                "conditions": {
                    "on_success": fake.boolean(),
                    "on_failure": True,
                    "on_retry": fake.boolean()
                }
            }
        })
    
    return base_config


class TaskParameterFactory(factory.django.DjangoModelFactory):
    """Factory pour TaskParameter"""
    
    class Meta:
        model = TaskParameter

    id = factory.Faker('uuid4')
    task = factory.SubFactory(TaskFactory)
    name = factory.Faker('word')
    parameter_type = factory.Faker('random_element', elements=[
        'string', 'integer', 'float', 'boolean', 'json', 'date', 'datetime', 'file'
    ])
    is_required = factory.Faker('boolean', chance_of_getting_true=70)
    description = factory.Faker('text', max_nb_chars=200)
    
    @factory.lazy_attribute
    def value(self):
        if self.parameter_type == 'string':
            return fake.word()
        elif self.parameter_type == 'integer':
            return str(fake.random_int(1, 1000))
        elif self.parameter_type == 'float':
            return str(fake.random.uniform(0.1, 999.9))
        elif self.parameter_type == 'boolean':
            return str(fake.boolean())
        elif self.parameter_type == 'json':
            return str({
                'key1': fake.word(),
                'key2': fake.random_int(1, 100),
                'key3': fake.boolean()
            })
        elif self.parameter_type == 'date':
            return fake.date().isoformat()
        elif self.parameter_type == 'datetime':
            return fake.date_time().isoformat()
        elif self.parameter_type == 'file':
            return fake.file_path()
        return fake.word()


class TaskDependencyFactory(factory.django.DjangoModelFactory):
    """Factory pour TaskDependency"""
    
    class Meta:
        model = TaskDependency

    id = factory.Faker('uuid4')
    task = factory.SubFactory(TaskFactory)
    depends_on = factory.SubFactory(TaskFactory)
    dependency_type = factory.Faker('random_element', elements=[
        'success', 'failure', 'completion', 'skip'
    ])


# Factories spécialisées pour différents types de tâches

class SQLExtractionTaskFactory(TaskFactory):
    """Factory pour tâche d'extraction SQL"""
    task_type = TaskType.EXTRACT
    name = factory.LazyAttribute(lambda obj: f"Extract {fake.word().title()}")
    
    config = factory.LazyFunction(lambda: {
        "source": {
            "type": "database",
            "connection_id": fake.uuid4(),
            "query": f"SELECT * FROM {fake.word()} WHERE updated_at > '{{{{ watermark }}}}'",
            "incremental": True,
            "watermark_column": "updated_at"
        },
        "output": {
            "format": "parquet",
            "compression": "snappy",
            "partitioning": True
        },
        "performance": {
            "batch_size": 50000,
            "parallel_workers": 4,
            "memory_limit_mb": 2048
        }
    })


class PythonTransformTaskFactory(TaskFactory):
    """Factory pour tâche de transformation Python"""
    task_type = TaskType.TRANSFORM
    name = factory.LazyAttribute(lambda obj: f"Transform {fake.word().title()}")
    
    config = factory.LazyFunction(lambda: {
        "transformation": {
            "engine": "python",
            "script": """
import pandas as pd

def transform(df):
    # Nettoyage des données
    df = df.dropna()
    df = df.drop_duplicates()
    
    # Transformations
    df['processed_at'] = pd.Timestamp.now()
    
    return df
            """,
            "functions": ["clean_data", "normalize", "aggregate"]
        },
        "validation": {
            "schema_check": True,
            "quality_rules": ["not_null", "unique"]
        }
    })


class DatabaseLoadTaskFactory(TaskFactory):
    """Factory pour tâche de chargement en base"""
    task_type = TaskType.LOAD
    name = factory.LazyAttribute(lambda obj: f"Load {fake.word().title()}")
    
    config = factory.LazyFunction(lambda: {
        "target": {
            "type": "database",
            "connection_id": fake.uuid4(),
            "table_name": fake.word(),
            "schema": "analytics"
        },
        "loading": {
            "strategy": "upsert",
            "batch_size": 10000,
            "create_indexes": True,
            "vacuum_after": True
        }
    })


# Factory pour créer un ensemble de tâches cohérentes

class TaskSetFactory:
    """Factory pour créer un ensemble de tâches cohérentes"""
    
    @classmethod
    def create_etl_task_set(cls, pipeline_step):
        """Crée un ensemble de tâches ETL pour une étape de pipeline"""
        tasks = []
        
        if pipeline_step.step_type == 'extract':
            # Tâche d'extraction principale
            extract_task = SQLExtractionTaskFactory(
                pipeline_step=pipeline_step,
                name=f"Extract {fake.word().title()} Data",
                order_index=1
            )
            tasks.append(extract_task)
            
            # Paramètres pour l'extraction
            TaskParameterFactory(
                task=extract_task,
                name="source_table",
                parameter_type="string",
                value=fake.word(),
                is_required=True
            )
            
            TaskParameterFactory(
                task=extract_task,
                name="batch_size",
                parameter_type="integer",
                value="10000",
                is_required=False
            )
        
        elif pipeline_step.step_type == 'transform':
            # Tâche de transformation
            transform_task = PythonTransformTaskFactory(
                pipeline_step=pipeline_step,
                name=f"Transform {fake.word().title()}",
                order_index=1
            )
            tasks.append(transform_task)
            
            # Paramètres pour la transformation
            TaskParameterFactory(
                task=transform_task,
                name="transformation_rules",
                parameter_type="json",
                value=str({
                    "clean_nulls": True,
                    "remove_duplicates": True,
                    "normalize_dates": True
                }),
                is_required=True
            )
        
        elif pipeline_step.step_type == 'load':
            # Tâche de chargement
            load_task = DatabaseLoadTaskFactory(
                pipeline_step=pipeline_step,
                name=f"Load to {fake.word().title()}",
                order_index=1
            )
            tasks.append(load_task)
            
            # Paramètres pour le chargement
            TaskParameterFactory(
                task=load_task,
                name="target_schema",
                parameter_type="string",
                value="analytics",
                is_required=True
            )
        
        return tasks
