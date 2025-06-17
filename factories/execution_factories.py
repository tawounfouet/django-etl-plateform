"""
Factories pour les modèles d'exécution
"""
import factory
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from apps.execution.models import (
    PipelineRun, TaskRun, ExecutionQueue, ExecutionLock, DataLineage,
    RunStatus, TriggerType
)
from .pipelines_factories import PipelineFactory, PipelineStepFactory
from .tasks_factories import TaskFactory
from .authentication_factories import CustomUserFactory

fake = Faker('fr_FR')


class PipelineRunFactory(factory.django.DjangoModelFactory):
    """Factory pour PipelineRun"""
    
    class Meta:
        model = PipelineRun

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    triggered_by = factory.SubFactory(CustomUserFactory)
    status = factory.Faker('random_element', elements=[
        RunStatus.PENDING,
        RunStatus.RUNNING,
        RunStatus.SUCCESS,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
        RunStatus.TIMEOUT,
        RunStatus.SKIPPED,
    ])
    trigger_type = factory.Faker('random_element', elements=[
        TriggerType.MANUAL,
        TriggerType.SCHEDULED,
        TriggerType.API,
        TriggerType.WEBHOOK,
        TriggerType.DEPENDENCY,
    ])
    
    @factory.lazy_attribute
    def completed_at(self):
        if self.status in [RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMEOUT]:
            # Use timezone.now() as base time since started_at is auto-generated
            base_time = timezone.now()
            return base_time + timedelta(
                minutes=fake.random_int(1, 120),
                seconds=fake.random_int(0, 59)
            )
        return None
    
    context = factory.LazyFunction(lambda: {
        'execution_id': fake.uuid4(),
        'environment': fake.random_element(['dev', 'staging', 'prod']),
        'executor': fake.random_element(['local', 'docker', 'kubernetes']),
        'version': fake.random_element(['1.0.0', '1.1.0', '2.0.0']),
        'parameters': {
            'batch_date': fake.date_object().isoformat(),
            'processing_mode': fake.random_element(['full', 'incremental']),
            'debug_enabled': fake.boolean(),
        },
        'resources': {
            'allocated_memory_mb': fake.random_int(512, 8192),
            'allocated_cpu_cores': fake.random_int(1, 8),
            'worker_nodes': fake.random_int(1, 5),
        },
        'external_refs': {
            'job_id': fake.uuid4(),
            'cluster_id': fake.uuid4(),
            'session_id': fake.uuid4(),
        }
    })
    
    metrics = factory.LazyAttribute(lambda obj: _generate_pipeline_metrics(obj.status))
    
    @factory.lazy_attribute
    def error_message(self):
        if self.status == RunStatus.FAILED:
            return fake.random_element([
                "Connection timeout to database",
                "Invalid data format in source file",
                "Memory limit exceeded during processing",
                "Authentication failed for external API",
                "Data quality validation failed",
                "Target table not found",
                "Insufficient disk space",
                "Network connectivity issue"
            ])
        return ""
    
    log_file_path = factory.LazyAttribute(
        lambda obj: f"/logs/pipelines/{obj.pipeline.name}/{timezone.now().strftime('%Y/%m/%d')}/{obj.id}.log"
    )


def _generate_pipeline_metrics(status):
    """Génère des métriques réalistes selon le statut"""
    base_metrics = {
        'execution_time_seconds': fake.random_int(60, 7200),
        'memory_usage_mb': fake.random_int(256, 4096),
        'cpu_usage_percent': fake.random_int(10, 95),
        'network_io_mb': fake.random_int(10, 1000),
        'disk_io_mb': fake.random_int(100, 5000),
    }
    
    if status == RunStatus.SUCCESS:
        base_metrics.update({
            'records_processed': fake.random_int(1000, 1000000),
            'records_inserted': fake.random_int(500, 500000),
            'records_updated': fake.random_int(100, 100000),
            'records_skipped': fake.random_int(0, 10000),
            'data_quality_score': fake.random.uniform(0.85, 1.0),
            'throughput_records_per_second': fake.random_int(100, 10000),
        })
    elif status == RunStatus.FAILED:
        base_metrics.update({
            'records_processed': fake.random_int(0, 50000),
            'error_count': fake.random_int(1, 100),
            'last_successful_step': fake.random_int(0, 5),
        })
    
    return base_metrics


class TaskRunFactory(factory.django.DjangoModelFactory):
    """Factory pour TaskRun"""
    
    class Meta:
        model = TaskRun

    id = factory.Faker('uuid4')
    pipeline_run = factory.SubFactory(PipelineRunFactory)
    pipeline_step = factory.SubFactory(PipelineStepFactory)
    task = factory.SubFactory(TaskFactory)
    status = factory.Faker('random_element', elements=[
        RunStatus.PENDING,
        RunStatus.RUNNING,
        RunStatus.SUCCESS,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
        RunStatus.SKIPPED,
    ])
    retry_count = factory.Faker('random_int', min=0, max=3)
    worker_id = factory.Faker('uuid4')
    
    @factory.lazy_attribute
    def started_at(self):
        if self.status != RunStatus.PENDING:
            # Use current time as base since pipeline_run.started_at is auto-generated
            base_time = timezone.now()
            return base_time + timedelta(
                minutes=fake.random_int(0, 30)
            )
        return None
    
    @factory.lazy_attribute
    def completed_at(self):
        if self.status in [RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.SKIPPED]:
            return self.started_at + timedelta(
                minutes=fake.random_int(1, 60),
                seconds=fake.random_int(0, 59)
            ) if self.started_at else None
        return None
    
    input_data = factory.LazyFunction(lambda: {
        'source_records': fake.random_int(1000, 100000),
        'source_size_mb': fake.random_int(10, 1000),
        'input_schema': {
            'columns': fake.words(nb=fake.random_int(5, 20)),
            'data_types': ['string', 'integer', 'float', 'datetime', 'boolean'],
        },
        'data_quality': {
            'null_percentage': fake.random.uniform(0, 0.1),
            'duplicate_percentage': fake.random.uniform(0, 0.05),
        }
    })
    
    output_data = factory.LazyAttribute(lambda obj: _generate_task_output(obj.status))
    
    logs = factory.LazyAttribute(lambda obj: _generate_task_logs(obj.status))
    
    metrics = factory.LazyAttribute(lambda obj: _generate_task_metrics(obj.status))
    
    @factory.lazy_attribute
    def error_message(self):
        if self.status == RunStatus.FAILED:
            return fake.random_element([
                "SQL syntax error in query",
                "File not found at specified path",
                "API rate limit exceeded",
                "Data type conversion error",
                "Validation rule violation",
                "Connection lost during execution",
                "Permission denied on target table",
                "Resource allocation timeout"
            ])
        return ""


def _generate_task_output(status):
    """Génère des données de sortie selon le statut"""
    if status == RunStatus.SUCCESS:
        return {
            'output_records': fake.random_int(500, 50000),
            'output_size_mb': fake.random_int(5, 500),
            'output_path': fake.file_path(depth=3),
            'checksum': fake.sha256(),
            'schema_changes': fake.boolean(),
        }
    elif status == RunStatus.FAILED:
        return {
            'partial_output_records': fake.random_int(0, 1000),
            'error_records': fake.random_int(1, 100),
        }
    return None


def _generate_task_logs(status):
    """Génère des logs réalistes selon le statut"""
    base_logs = [
        f"[{fake.date_time()}] INFO: Task started",
        f"[{fake.date_time()}] INFO: Initializing connections",
        f"[{fake.date_time()}] INFO: Processing data batch 1",
    ]
    
    if status == RunStatus.SUCCESS:
        base_logs.extend([
            f"[{fake.date_time()}] INFO: Processing completed successfully",
            f"[{fake.date_time()}] INFO: Records processed: {fake.random_int(1000, 100000)}",
            f"[{fake.date_time()}] INFO: Task completed",
        ])
    elif status == RunStatus.FAILED:
        base_logs.extend([
            f"[{fake.date_time()}] ERROR: {fake.sentence()}",
            f"[{fake.date_time()}] ERROR: Task failed with errors",
        ])
    
    return "\n".join(base_logs)


def _generate_task_metrics(status):
    """Génère des métriques de tâche selon le statut"""
    base_metrics = {
        'execution_time_seconds': fake.random_int(10, 1800),
        'memory_peak_mb': fake.random_int(128, 2048),
        'cpu_avg_percent': fake.random_int(20, 90),
        'io_read_mb': fake.random_int(10, 500),
        'io_write_mb': fake.random_int(5, 250),
    }
    
    if status == RunStatus.SUCCESS:
        base_metrics.update({
            'records_per_second': fake.random_int(50, 5000),
            'success_rate': 1.0,
            'data_quality_score': fake.random.uniform(0.8, 1.0),
        })
    elif status == RunStatus.FAILED:
        base_metrics.update({
            'success_rate': 0.0,
            'error_rate': fake.random.uniform(0.1, 1.0),
        })
    
    return base_metrics


class ExecutionQueueFactory(factory.django.DjangoModelFactory):
    """Factory pour ExecutionQueue"""
    
    class Meta:
        model = ExecutionQueue

    id = factory.Faker('uuid4')
    pipeline_run = factory.SubFactory(PipelineRunFactory, status=RunStatus.PENDING)
    priority = factory.Faker('random_element', elements=[1, 2, 3, 4, 5])  # 1=LOW, 5=CRITICAL
    scheduled_at = factory.Faker('future_datetime', end_date='+1h')


class ExecutionLockFactory(factory.django.DjangoModelFactory):
    """Factory pour ExecutionLock"""
    
    class Meta:
        model = ExecutionLock

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    locked_by = factory.SubFactory(PipelineRunFactory, status=RunStatus.RUNNING)
    expires_at = factory.Faker('future_datetime', end_date='+2h')


class DataLineageFactory(factory.django.DjangoModelFactory):
    """Factory pour DataLineage"""
    
    class Meta:
        model = DataLineage

    id = factory.Faker('uuid4')
    source_task = factory.SubFactory(TaskRunFactory)
    target_task = factory.SubFactory(TaskRunFactory)
    relationship_type = factory.Faker('random_element', elements=[
        'direct', 'transformation', 'aggregation', 'join'
    ])
    
    metadata = factory.LazyFunction(lambda: {
        'columns_mapping': {
            fake.word(): fake.word() for _ in range(fake.random_int(1, 5))
        },
        'transformation_rules': fake.words(nb=fake.random_int(1, 3)),
        'data_flow': {
            'volume_mb': fake.random_int(1, 1000),
            'record_count': fake.random_int(100, 100000),
            'processing_time_seconds': fake.random_int(10, 600),
        },
        'quality_metrics': {
            'accuracy': fake.random.uniform(0.8, 1.0),
            'completeness': fake.random.uniform(0.9, 1.0),
            'consistency': fake.random.uniform(0.85, 1.0),
        }
    })


# Factories spécialisées pour différents scénarios d'exécution

class SuccessfulPipelineRunFactory(PipelineRunFactory):
    """Factory pour exécution réussie"""
    status = RunStatus.SUCCESS
    error_message = ""
    
    metrics = factory.LazyFunction(lambda: {
        'execution_time_seconds': fake.random_int(300, 3600),
        'memory_usage_mb': fake.random_int(512, 2048),
        'cpu_usage_percent': fake.random_int(30, 70),
        'records_processed': fake.random_int(10000, 1000000),
        'records_inserted': fake.random_int(8000, 800000),
        'records_updated': fake.random_int(1000, 100000),
        'data_quality_score': fake.random.uniform(0.9, 1.0),
        'throughput_records_per_second': fake.random_int(500, 5000),
    })


class FailedPipelineRunFactory(PipelineRunFactory):
    """Factory pour exécution échouée"""
    status = RunStatus.FAILED
    
    metrics = factory.LazyFunction(lambda: {
        'execution_time_seconds': fake.random_int(60, 1800),
        'memory_usage_mb': fake.random_int(256, 1024),
        'cpu_usage_percent': fake.random_int(10, 50),
        'records_processed': fake.random_int(0, 10000),
        'error_count': fake.random_int(1, 50),
        'last_successful_step': fake.random_int(0, 3),
    })


class LongRunningPipelineRunFactory(PipelineRunFactory):
    """Factory pour exécution longue"""
    status = RunStatus.RUNNING
    trigger_type = TriggerType.SCHEDULED
    
    context = factory.LazyFunction(lambda: {
        'execution_id': fake.uuid4(),
        'environment': 'prod',
        'executor': 'kubernetes',
        'parameters': {
            'batch_date': fake.date_object().isoformat(),
            'processing_mode': 'full',
            'large_dataset': True,
        },
        'resources': {
            'allocated_memory_mb': 8192,
            'allocated_cpu_cores': 8,
            'worker_nodes': 5,
        }
    })


# Factory pour créer un ensemble complet d'exécutions

class ExecutionHistoryFactory:
    """Factory pour créer un historique d'exécutions"""
    
    @classmethod
    def create_pipeline_history(cls, pipeline, days=30):
        """Crée un historique d'exécutions pour un pipeline"""
        runs = []
        current_date = timezone.now()
        
        for day in range(days):
            run_date = current_date - timedelta(days=day)
            
            # Simuler différents scénarios d'exécution
            scenario = fake.random_element([
                'success', 'success', 'success', 'success',  # 80% de succès
                'failed', 'timeout'  # 20% d'échecs
            ])
            
            if scenario == 'success':
                run = SuccessfulPipelineRunFactory(
                    pipeline=pipeline,
                    started_at=run_date,
                    trigger_type=TriggerType.SCHEDULED
                )
            elif scenario == 'failed':
                run = FailedPipelineRunFactory(
                    pipeline=pipeline,
                    started_at=run_date,
                    trigger_type=TriggerType.SCHEDULED
                )
            else:  # timeout
                run = PipelineRunFactory(
                    pipeline=pipeline,
                    started_at=run_date,
                    status=RunStatus.TIMEOUT,
                    trigger_type=TriggerType.SCHEDULED
                )
            
            runs.append(run)
            
            # Créer des task runs pour chaque pipeline run
            for step in pipeline.steps.all():
                task_status = RunStatus.SUCCESS if run.status == RunStatus.SUCCESS else fake.random_element([
                    RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.SKIPPED
                ])
                
                TaskRunFactory(
                    pipeline_run=run,
                    pipeline_step=step,
                    status=task_status,
                    started_at=run.started_at + timedelta(minutes=fake.random_int(0, 10)),
                )
        
        return runs
