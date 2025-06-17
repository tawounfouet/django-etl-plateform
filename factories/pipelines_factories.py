"""
Factories pour les modèles de pipelines
"""
import factory
from faker import Faker
from apps.pipelines.models import (
    Pipeline, PipelineStep, PipelineSchedule, 
    PipelineTag, PipelineTagAssignment,
    PipelineStatus, StepType
)
from .core_factories import OrganizationFactory
from .authentication_factories import CustomUserFactory

fake = Faker('fr_FR')


class PipelineFactory(factory.django.DjangoModelFactory):
    """Factory pour Pipeline"""
    
    class Meta:
        model = Pipeline

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=500)
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(CustomUserFactory)
    status = factory.Faker('random_element', elements=[
        PipelineStatus.DRAFT,
        PipelineStatus.ACTIVE,
        PipelineStatus.PAUSED,
        PipelineStatus.DEPRECATED,
    ])
    version = factory.Faker('random_element', elements=[
        '1.0.0', '1.1.0', '1.2.0', '2.0.0', '2.1.0'
    ])
    
    config = factory.LazyFunction(lambda: {
        'max_retries': fake.random_int(1, 5),
        'retry_delay_seconds': fake.random_int(30, 300),
        'timeout_minutes': fake.random_int(30, 1440),
        'parallel_execution': fake.boolean(),
        'failure_handling': fake.random_element(['stop', 'continue', 'skip']),
        'notification_settings': {
            'on_success': fake.boolean(),
            'on_failure': True,
            'on_retry': fake.boolean(),
            'channels': fake.random_elements(['email', 'slack', 'webhook'], length=2)
        },
        'resource_limits': {
            'max_memory_mb': fake.random_int(512, 8192),
            'max_cpu_cores': fake.random_int(1, 8),
            'max_runtime_minutes': fake.random_int(60, 720)
        },
        'data_validation': {
            'schema_validation': fake.boolean(),
            'quality_checks': fake.boolean(),
            'anomaly_detection': fake.boolean()
        }
    })
    
    metadata = factory.LazyFunction(lambda: {
        'category': fake.random_element([
            'data_ingestion', 'data_transformation', 'data_export',
            'monitoring', 'maintenance', 'reporting'
        ]),
        'priority': fake.random_element(['low', 'medium', 'high', 'critical']),
        'business_impact': fake.random_element(['low', 'medium', 'high']),
        'data_sensitivity': fake.random_element(['public', 'internal', 'confidential']),
        'owner_team': fake.random_element(['data', 'analytics', 'engineering']),
        'stakeholders': [fake.email() for _ in range(fake.random_int(1, 3))],
        'documentation_url': fake.url(),
        'slack_channel': f"#{fake.word()}-{fake.word()}",
        'cost_center': fake.random_element(['IT', 'Analytics', 'Operations']),
        'compliance_requirements': fake.random_elements([
            'GDPR', 'HIPAA', 'SOX', 'PCI-DSS'
        ], length=fake.random_int(0, 2))
    })


class PipelineStepFactory(factory.django.DjangoModelFactory):
    """Factory pour PipelineStep"""
    
    class Meta:
        model = PipelineStep

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    name = factory.Faker('word')
    order_index = factory.Sequence(lambda n: n)
    step_type = factory.Faker('random_element', elements=[
        StepType.EXTRACT,
        StepType.TRANSFORM,
        StepType.LOAD,
        StepType.VALIDATE,
        StepType.NOTIFY,
    ])
    is_parallel = factory.Faker('boolean', chance_of_getting_true=30)
    
    config = factory.LazyAttribute(lambda obj: {
        'step_type': obj.step_type,
        'description': fake.text(max_nb_chars=200),
        'timeout_seconds': fake.random_int(60, 3600),
        'retry_count': fake.random_int(0, 3),
        'conditions': {
            'run_if': fake.random_element(['always', 'on_success', 'on_failure']),
            'skip_if_empty': fake.boolean(),
        },
        'parameters': _generate_step_config(obj.step_type),
        'outputs': {
            'save_intermediate': fake.boolean(),
            'output_format': fake.random_element(['json', 'csv', 'parquet']),
            'compression': fake.random_element(['none', 'gzip', 'snappy'])
        }
    })
    
    dependencies = factory.LazyFunction(lambda: [])


def _generate_step_config(step_type):
    """Génère une configuration spécifique selon le type d'étape"""
    if step_type == StepType.EXTRACT:
        return {
            'source_type': fake.random_element(['database', 'api', 'file', 'cloud']),
            'query_timeout': fake.random_int(30, 300),
            'batch_size': fake.random_int(1000, 100000),
            'incremental': fake.boolean(),
            'watermark_column': fake.random_element(['updated_at', 'created_at', 'id']),
        }
    elif step_type == StepType.TRANSFORM:
        return {
            'transformation_type': fake.random_element(['sql', 'python', 'spark']),
            'memory_limit_mb': fake.random_int(512, 4096),
            'operations': fake.random_elements([
                'filter', 'aggregate', 'join', 'pivot', 'clean'
            ], length=fake.random_int(1, 3)),
        }
    elif step_type == StepType.LOAD:
        return {
            'target_type': fake.random_element(['database', 'file', 'cloud', 'api']),
            'load_strategy': fake.random_element(['insert', 'upsert', 'replace']),
            'batch_size': fake.random_int(1000, 50000),
            'create_indexes': fake.boolean(),
        }
    elif step_type == StepType.VALIDATE:
        return {
            'validation_rules': fake.random_elements([
                'not_null', 'unique', 'range_check', 'format_check'
            ], length=fake.random_int(1, 4)),
            'tolerance_threshold': fake.random_int(0, 10),
            'action_on_failure': fake.random_element(['stop', 'warn', 'quarantine']),
        }
    elif step_type == StepType.NOTIFY:
        return {
            'notification_type': fake.random_element(['email', 'slack', 'webhook']),
            'recipients': [fake.email() for _ in range(fake.random_int(1, 5))],
            'template': fake.random_element(['success', 'failure', 'warning']),
        }
    return {}


class PipelineScheduleFactory(factory.django.DjangoModelFactory):
    """Factory pour PipelineSchedule"""
    
    class Meta:
        model = PipelineSchedule

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    schedule_type = factory.Faker('random_element', elements=[
        'manual', 'cron', 'interval', 'event'
    ])
    is_active = factory.Faker('boolean', chance_of_getting_true=80)
    timezone = factory.Faker('random_element', elements=[
        'UTC', 'Europe/Paris', 'America/New_York', 'Asia/Tokyo'
    ])
    next_run = factory.Faker('future_datetime', end_date='+30d')
    
    @factory.lazy_attribute
    def cron_expression(self):
        if self.schedule_type == 'cron':
            # Générer des expressions cron communes
            return fake.random_element([
                '0 2 * * *',      # Tous les jours à 2h
                '0 */6 * * *',    # Toutes les 6 heures
                '0 8 * * 1',      # Tous les lundis à 8h
                '0 0 1 * *',      # Le 1er de chaque mois
                '*/15 * * * *',   # Toutes les 15 minutes
                '0 9,17 * * 1-5', # 9h et 17h en semaine
            ])
        return ''
    
    @factory.lazy_attribute
    def interval_minutes(self):
        if self.schedule_type == 'interval':
            return fake.random_element([15, 30, 60, 120, 240, 480, 1440])
        return None


class PipelineTagFactory(factory.django.DjangoModelFactory):
    """Factory pour PipelineTag"""
    
    class Meta:
        model = PipelineTag
        django_get_or_create = ('name', 'organization')

    id = factory.Faker('uuid4')
    name = factory.Faker('random_element', elements=[
        'production', 'staging', 'development', 'critical', 'daily',
        'weekly', 'monthly', 'real-time', 'batch', 'streaming',
        'sales', 'marketing', 'finance', 'hr', 'operations',
        'experimental', 'deprecated', 'maintenance', 'monitoring'
    ])
    color = factory.Faker('random_element', elements=[
        '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
        '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
    ])
    organization = factory.SubFactory(OrganizationFactory)


class PipelineTagAssignmentFactory(factory.django.DjangoModelFactory):
    """Factory pour PipelineTagAssignment"""
    
    class Meta:
        model = PipelineTagAssignment

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    tag = factory.SubFactory(PipelineTagFactory)
    assigned_by = factory.SubFactory(CustomUserFactory)


# Factories spécialisées pour différents types de pipelines

class DataIngestionPipelineFactory(PipelineFactory):
    """Factory pour pipeline d'ingestion de données"""
    name = factory.LazyAttribute(lambda obj: f"Ingestion {fake.word().title()}")
    description = "Pipeline d'ingestion de données depuis une source externe"
    
    metadata = factory.LazyFunction(lambda: {
        'category': 'data_ingestion',
        'priority': 'high',
        'business_impact': 'high',
        'data_sensitivity': 'confidential',
        'frequency': 'daily',
        'data_volume': fake.random_element(['small', 'medium', 'large']),
        'source_systems': fake.random_elements([
            'CRM', 'ERP', 'Marketing', 'Sales', 'Support'
        ], length=fake.random_int(1, 3))
    })


class DataTransformationPipelineFactory(PipelineFactory):
    """Factory pour pipeline de transformation"""
    name = factory.LazyAttribute(lambda obj: f"Transform {fake.word().title()}")
    description = "Pipeline de transformation et enrichissement des données"
    
    metadata = factory.LazyFunction(lambda: {
        'category': 'data_transformation',
        'priority': 'medium',
        'business_impact': 'medium',
        'complexity': fake.random_element(['low', 'medium', 'high']),
        'transformation_type': fake.random_element([
            'aggregation', 'cleaning', 'enrichment', 'normalization'
        ])
    })


class ReportingPipelineFactory(PipelineFactory):
    """Factory pour pipeline de reporting"""
    name = factory.LazyAttribute(lambda obj: f"Report {fake.word().title()}")
    description = "Pipeline de génération de rapports automatisés"
    
    metadata = factory.LazyFunction(lambda: {
        'category': 'reporting',
        'priority': 'low',
        'business_impact': 'medium',
        'report_frequency': fake.random_element(['daily', 'weekly', 'monthly']),
        'recipients': [fake.email() for _ in range(fake.random_int(1, 3))],
        'format': fake.random_element(['pdf', 'excel', 'dashboard'])
    })


# Factory pour créer un pipeline complet avec ses étapes

class CompletePipelineFactory(PipelineFactory):
    """Factory qui crée un pipeline complet avec étapes et planification"""
    
    @factory.post_generation
    def create_steps(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Créer les étapes dans l'ordre logique
        extract_step = PipelineStepFactory(
            pipeline=self,
            name='Extract Data',
            step_type=StepType.EXTRACT,
            order_index=1
        )
        
        transform_step = PipelineStepFactory(
            pipeline=self,
            name='Transform Data',
            step_type=StepType.TRANSFORM,
            order_index=2,
            dependencies=[str(extract_step.id)]
        )
        
        validate_step = PipelineStepFactory(
            pipeline=self,
            name='Validate Data',
            step_type=StepType.VALIDATE,
            order_index=3,
            dependencies=[str(transform_step.id)]
        )
        
        load_step = PipelineStepFactory(
            pipeline=self,
            name='Load Data',
            step_type=StepType.LOAD,
            order_index=4,
            dependencies=[str(validate_step.id)]
        )
        
        notify_step = PipelineStepFactory(
            pipeline=self,
            name='Send Notification',
            step_type=StepType.NOTIFY,
            order_index=5,
            dependencies=[str(load_step.id)]
        )
        
        # Créer une planification
        PipelineScheduleFactory(pipeline=self)
        
        # Ajouter quelques tags
        created_tags = []
        for tag_name in fake.random_elements([
            'production', 'daily', 'critical', 'automated'
        ], length=fake.random_int(1, 3), unique=True):
            # Essayer de récupérer un tag existant ou en créer un nouveau
            from apps.pipelines.models import PipelineTag
            tag, created = PipelineTag.objects.get_or_create(
                name=tag_name, 
                organization=self.organization
            )
            if tag not in created_tags:
                created_tags.append(tag)
                # Créer l'assignation seulement si elle n'existe pas déjà
                from apps.pipelines.models import PipelineTagAssignment
                assignment, created = PipelineTagAssignment.objects.get_or_create(
                    pipeline=self,
                    tag=tag,
                    defaults={'assigned_by': self.created_by}
                )
