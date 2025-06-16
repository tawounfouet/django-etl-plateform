# Optimisation des Performances - Django ETL Platform

## Vue d'ensemble

L'optimisation des performances est cruciale pour une plateforme ETL qui doit traiter de gros volumes de données de manière efficace. Ce guide couvre les stratégies d'optimisation à tous les niveaux de l'architecture.

## Optimisations base de données

### Index et requêtes optimisées

#### Index composites stratégiques
```python
# models.py
class PipelineRun(models.Model):
    # ...existing fields...
    
    class Meta:
        db_table = 'pipeline_runs'
        indexes = [
            # Index pour dashboard principal
            models.Index(
                fields=['pipeline', '-started_at', 'status'],
                name='pipeline_runs_dashboard_idx'
            ),
            # Index pour recherche par période
            models.Index(
                fields=['started_at', 'status'],
                condition=models.Q(status__in=['running', 'pending']),
                name='active_runs_by_date_idx'
            ),
            # Index partiel pour runs récents
            models.Index(
                fields=['-started_at'],
                condition=models.Q(started_at__gte=timezone.now() - timedelta(days=30)),
                name='recent_runs_idx'
            ),
        ]
```

#### Optimisation des requêtes ORM
```python
# Mauvais: N+1 queries
def get_pipelines_with_last_run():
    pipelines = Pipeline.objects.all()
    for pipeline in pipelines:
        last_run = pipeline.runs.order_by('-started_at').first()
        print(f"{pipeline.name}: {last_run.status if last_run else 'No runs'}")

# Bon: Query optimisée avec subquery
from django.db.models import OuterRef, Subquery

def get_pipelines_with_last_run_optimized():
    last_run = PipelineRun.objects.filter(
        pipeline=OuterRef('pk')
    ).order_by('-started_at').values('status')[:1]
    
    pipelines = Pipeline.objects.annotate(
        last_run_status=Subquery(last_run)
    ).prefetch_related('steps')
    
    return pipelines

# Excellent: Avec cache Redis
from django.core.cache import cache

def get_pipelines_with_cache():
    cache_key = 'pipelines_with_last_run'
    result = cache.get(cache_key)
    
    if result is None:
        result = list(get_pipelines_with_last_run_optimized())
        cache.set(cache_key, result, timeout=300)  # 5 minutes
    
    return result
```

### Partitioning de tables

#### Partitioning par date pour TaskRun
```sql
-- PostgreSQL partitioning
CREATE TABLE task_runs_partitioned (
    LIKE task_runs INCLUDING ALL
) PARTITION BY RANGE (started_at);

-- Partitions mensuelles
CREATE TABLE task_runs_2025_01 PARTITION OF task_runs_partitioned
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE task_runs_2025_02 PARTITION OF task_runs_partitioned
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Script automatique de création de partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

#### Django management command pour partitions
```python
# management/commands/create_partitions.py
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create monthly partitions for task_runs table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months-ahead',
            type=int,
            default=3,
            help='Number of months ahead to create partitions'
        )

    def handle(self, *args, **options):
        months_ahead = options['months_ahead']
        
        with connection.cursor() as cursor:
            for i in range(months_ahead):
                date = datetime.now().replace(day=1) + timedelta(days=32 * i)
                partition_date = date.replace(day=1)
                
                cursor.execute(
                    "SELECT create_monthly_partition('task_runs_partitioned', %s)",
                    [partition_date]
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created partition for {partition_date.strftime("%Y-%m")}'
                    )
                )
```

### Connection pooling

#### Configuration PgBouncer
```ini
# pgbouncer.ini
[databases]
etl_platform = host=postgres port=5432 dbname=etl_platform user=etl_user

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = trust
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5

# Performance tuning
server_lifetime = 3600
server_idle_timeout = 600
client_idle_timeout = 0
```

#### Django settings pour connection pooling
```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'etl_platform',
        'USER': 'etl_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'pgbouncer',
        'PORT': '6432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 600,  # 10 minutes
        },
        'TEST': {
            'NAME': 'test_etl_platform',
        }
    }
}

# Connection pooling avec django-db-pool
DATABASES['default']['ENGINE'] = 'django_db_pool.backends.postgresql'
DATABASES['default']['POOL_OPTIONS'] = {
    'POOL_SIZE': 10,
    'MAX_OVERFLOW': 10,
    'RECYCLE': 300,
}
```

## Optimisations application Django

### Mise en cache stratégique

#### Cache multi-niveaux
```python
# cache.py
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
import hashlib
import json

class MultiLevelCache:
    def __init__(self):
        self.memory_cache = {}  # Cache en mémoire local
        self.redis_cache = cache  # Cache Redis partagé
    
    def get(self, key, default=None):
        # Niveau 1: Mémoire locale (plus rapide)
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Niveau 2: Redis (partagé entre workers)
        value = self.redis_cache.get(key, default)
        if value is not default:
            self.memory_cache[key] = value
        
        return value
    
    def set(self, key, value, timeout=DEFAULT_TIMEOUT):
        self.memory_cache[key] = value
        self.redis_cache.set(key, value, timeout)
    
    def delete(self, key):
        self.memory_cache.pop(key, None)
        self.redis_cache.delete(key)

# Usage dans services
class PipelineService:
    def __init__(self):
        self.cache = MultiLevelCache()
    
    def get_pipeline_config(self, pipeline_id):
        cache_key = f'pipeline_config:{pipeline_id}'
        config = self.cache.get(cache_key)
        
        if config is None:
            pipeline = Pipeline.objects.get(id=pipeline_id)
            config = pipeline.config
            # Cache pour 1 heure
            self.cache.set(cache_key, config, timeout=3600)
        
        return config
```

#### Cache invalidation intelligente
```python
# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Pipeline)
def invalidate_pipeline_cache(sender, instance, **kwargs):
    cache_keys_to_delete = [
        f'pipeline_config:{instance.id}',
        f'pipeline_steps:{instance.id}',
        'active_pipelines_list',
    ]
    
    cache.delete_many(cache_keys_to_delete)
    
    # Invalider cache des runs pour ce pipeline
    cache.delete_pattern(f'pipeline_runs:{instance.id}:*')

# Cache avec versioning pour éviter l'invalidation
def get_versioned_cache_key(base_key, version_data):
    """Génère une clé de cache avec version basée sur les données"""
    version_hash = hashlib.md5(
        json.dumps(version_data, sort_keys=True).encode()
    ).hexdigest()[:8]
    return f'{base_key}:v{version_hash}'

def get_pipeline_with_steps(pipeline_id):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    version_data = {
        'pipeline_updated': pipeline.updated_at.isoformat(),
        'steps_count': pipeline.steps.count()
    }
    
    cache_key = get_versioned_cache_key(
        f'pipeline_with_steps:{pipeline_id}',
        version_data
    )
    
    result = cache.get(cache_key)
    if result is None:
        result = {
            'pipeline': pipeline,
            'steps': list(pipeline.steps.all())
        }
        cache.set(cache_key, result, timeout=1800)  # 30 minutes
    
    return result
```

### Optimisation des serializers

#### Serializers optimisés avec select_related
```python
# serializers.py
from rest_framework import serializers

class OptimizedPipelineSerializer(serializers.ModelSerializer):
    steps_count = serializers.SerializerMethodField()
    last_run = serializers.SerializerMethodField()
    
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'status', 'steps_count', 'last_run']
    
    def get_steps_count(self, obj):
        # Utilise le prefetch_related pour éviter les requêtes supplémentaires
        return len(obj.prefetched_steps) if hasattr(obj, 'prefetched_steps') else obj.steps.count()
    
    def get_last_run(self, obj):
        # Utilise le prefetch_related avec ordering
        if hasattr(obj, 'prefetched_runs') and obj.prefetched_runs:
            last_run = obj.prefetched_runs[0]
            return {
                'id': last_run.id,
                'status': last_run.status,
                'started_at': last_run.started_at
            }
        return None

# ViewSet optimisé
class PipelineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OptimizedPipelineSerializer
    
    def get_queryset(self):
        return Pipeline.objects.select_related(
            'created_by', 'organization'
        ).prefetch_related(
            'steps',
            Prefetch(
                'runs',
                queryset=PipelineRun.objects.order_by('-started_at')[:1],
                to_attr='prefetched_runs'
            )
        )
```

## Optimisations Celery

### Configuration pour haute performance

#### Optimisation des workers
```python
# celery_config.py
from celery import Celery
from kombu import Queue, Exchange

app = Celery('etl_platform')

# Configuration optimisée
app.conf.update(
    # Serialization
    task_serializer='msgpack',
    result_serializer='msgpack',
    accept_content=['msgpack'],
    
    # Performance
    worker_prefetch_multiplier=1,  # Pour les tâches longues
    task_acks_late=True,
    worker_disable_rate_limits=True,
    
    # Connection pool
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    
    # Routing
    task_routes={
        'apps.tasks.extract.*': {'queue': 'extract'},
        'apps.tasks.transform.*': {'queue': 'transform'},
        'apps.tasks.load.*': {'queue': 'load'},
        'apps.tasks.notify.*': {'queue': 'notifications'},
    },
    
    # Queues avec priorités
    task_default_queue='default',
    task_queues=(
        Queue('extract', Exchange('extract'), routing_key='extract', 
              queue_arguments={'x-max-priority': 10}),
        Queue('transform', Exchange('transform'), routing_key='transform',
              queue_arguments={'x-max-priority': 5}),
        Queue('load', Exchange('load'), routing_key='load',
              queue_arguments={'x-max-priority': 3}),
        Queue('notifications', Exchange('notifications'), routing_key='notifications',
              queue_arguments={'x-max-priority': 1}),
    ),
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)
```

#### Workers spécialisés
```python
# tasks/base.py
from celery import Task
import psutil
import logging

class ResourceMonitorTask(Task):
    """Task base avec monitoring des ressources"""
    
    def before_start(self, task_id, args, kwargs):
        self.start_memory = psutil.virtual_memory().used
        self.start_time = time.time()
        logging.info(f"Task {task_id} started", extra={
            'task_id': task_id,
            'memory_usage_mb': self.start_memory / 1024 / 1024
        })
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        end_memory = psutil.virtual_memory().used
        duration = time.time() - self.start_time
        
        logging.info(f"Task {task_id} completed", extra={
            'task_id': task_id,
            'status': status,
            'duration_seconds': duration,
            'memory_delta_mb': (end_memory - self.start_memory) / 1024 / 1024
        })

# Worker configuration par type de tâche
# start_extract_worker.sh
celery -A etl_platform worker \
    --queues=extract \
    --concurrency=2 \
    --max-memory-per-child=2048000 \
    --loglevel=info \
    --hostname=extract-worker@%h

# start_transform_worker.sh
celery -A etl_platform worker \
    --queues=transform \
    --concurrency=4 \
    --max-memory-per-child=1024000 \
    --loglevel=info \
    --hostname=transform-worker@%h
```

### Streaming et traitement par batch

#### Streaming pour gros volumes
```python
# tasks/streaming.py
from typing import Iterator, Generator
import pandas as pd

class StreamingDataProcessor:
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
    
    def process_large_dataset(self, connector: BaseConnector, query: str) -> Iterator[pd.DataFrame]:
        """Traite un gros dataset par chunks"""
        offset = 0
        
        while True:
            chunk_query = f"{query} LIMIT {self.chunk_size} OFFSET {offset}"
            chunk = connector.extract(chunk_query)
            
            if chunk.empty:
                break
                
            yield self.transform_chunk(chunk)
            offset += self.chunk_size
    
    def transform_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Applique les transformations sur un chunk"""
        # Transformations en place pour économiser la mémoire
        chunk.dropna(inplace=True)
        chunk['processed_at'] = pd.Timestamp.now()
        return chunk

@app.task(base=ResourceMonitorTask, bind=True)
def process_large_extract_task(self, connector_config: dict, query: str, destination_config: dict):
    """Tâche de traitement de gros volume avec streaming"""
    
    source_connector = ConnectorFactory.create(
        connector_config['type'], 
        connector_config
    )
    
    destination_connector = ConnectorFactory.create(
        destination_config['type'],
        destination_config
    )
    
    processor = StreamingDataProcessor(chunk_size=5000)
    total_processed = 0
    
    try:
        for chunk in processor.process_large_dataset(source_connector, query):
            # Charger le chunk transformé
            destination_connector.load(chunk)
            total_processed += len(chunk)
            
            # Mettre à jour le progress
            self.update_state(
                state='PROGRESS',
                meta={'processed': total_processed}
            )
            
            # Libérer la mémoire
            del chunk
    
    except Exception as e:
        logging.error(f"Error processing large dataset: {e}")
        raise
    
    return {'total_processed': total_processed}
```

## Optimisations frontend

### Lazy loading et pagination

#### Pagination intelligente pour dashboard
```python
# views.py
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

class TimestampCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-started_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size = 100

class PipelineRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PipelineRunSerializer
    pagination_class = TimestampCursorPagination
    
    def get_queryset(self):
        queryset = PipelineRun.objects.select_related(
            'pipeline', 'triggered_by'
        ).prefetch_related('task_runs')
        
        # Filtres optimisés
        pipeline_id = self.request.query_params.get('pipeline_id')
        if pipeline_id:
            queryset = queryset.filter(pipeline_id=pipeline_id)
            
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Endpoint optimisé pour les statistiques"""
        cache_key = 'pipeline_runs_stats'
        stats = cache.get(cache_key)
        
        if stats is None:
            queryset = self.get_queryset()
            stats = queryset.aggregate(
                total=Count('id'),
                running=Count('id', filter=Q(status='running')),
                success=Count('id', filter=Q(status='success')),
                failed=Count('id', filter=Q(status='failed')),
                avg_duration=Avg(
                    F('completed_at') - F('started_at'),
                    filter=Q(status='success')
                )
            )
            cache.set(cache_key, stats, timeout=60)  # 1 minute
        
        return Response(stats)
```

#### WebSocket pour updates temps réel
```python
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class PipelineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.pipeline_id = self.scope['url_route']['kwargs']['pipeline_id']
        self.room_group_name = f'pipeline_{self.pipeline_id}'
        
        # Joindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état initial
        initial_data = await self.get_pipeline_status()
        await self.send(text_data=json.dumps(initial_data))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def get_pipeline_status(self):
        # Optimiser cette requête
        pipeline = Pipeline.objects.select_related('organization').get(
            id=self.pipeline_id
        )
        
        latest_runs = pipeline.runs.order_by('-started_at')[:5]
        
        return {
            'pipeline': {
                'id': str(pipeline.id),
                'name': pipeline.name,
                'status': pipeline.status
            },
            'latest_runs': [
                {
                    'id': str(run.id),
                    'status': run.status,
                    'started_at': run.started_at.isoformat() if run.started_at else None
                } for run in latest_runs
            ]
        }
    
    async def pipeline_status_update(self, event):
        """Recevoir update du groupe"""
        await self.send(text_data=json.dumps(event['data']))

# Signal pour envoyer updates WebSocket
@receiver(post_save, sender=PipelineRun)
def pipeline_run_status_changed(sender, instance, **kwargs):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    group_name = f'pipeline_{instance.pipeline_id}'
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'pipeline_status_update',
            'data': {
                'run_id': str(instance.id),
                'status': instance.status,
                'started_at': instance.started_at.isoformat() if instance.started_at else None
            }
        }
    )
```

## Monitoring des performances

### Métriques personnalisées

#### Middleware de monitoring
```python
# middleware.py
import time
import logging
from django.db import connection
from django.core.cache import cache
from prometheus_client import Counter, Histogram, Gauge

# Métriques Prometheus
REQUEST_COUNT = Counter('django_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('django_http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('django_db_connections_active', 'Active database connections')
CACHE_OPERATIONS = Counter('django_cache_operations_total', 'Cache operations', ['operation', 'result'])

class PerformanceMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Compter les connexions DB avant
        queries_before = len(connection.queries)
        
        response = self.get_response(request)
        
        # Calculer les métriques
        duration = time.time() - start_time
        queries_count = len(connection.queries) - queries_before
        
        # Enregistrer les métriques
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=self.get_endpoint(request),
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.observe(duration)
        ACTIVE_CONNECTIONS.set(len(connection.queries))
        
        # Logger les requêtes lentes
        if duration > 1.0:  # Plus de 1 seconde
            logging.warning(f"Slow request: {request.path}", extra={
                'duration': duration,
                'queries_count': queries_count,
                'method': request.method,
                'status_code': response.status_code
            })
        
        return response
    
    def get_endpoint(self, request):
        """Extrait l'endpoint normalisé"""
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match:
            return f"{resolver_match.app_name}:{resolver_match.url_name}"
        return request.path
```

#### Profiling automatique
```python
# utils/profiling.py
import cProfile
import pstats
import io
from functools import wraps
from django.conf import settings

def profile_function(func):
    """Decorator pour profiler une fonction"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
            
            # Analyser les résultats
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative', 'calls')
            ps.print_stats(20)  # Top 20 functions
            
            logging.info(f"Profile for {func.__name__}:\n{s.getvalue()}")
        
        return result
    return wrapper

# Usage
@profile_function
def complex_pipeline_operation():
    # Code complexe à profiler
    pass
```

### Alertes de performance

#### Système d'alertes automatiques
```python
# monitoring/alerts.py
from dataclasses import dataclass
from typing import List
import logging

@dataclass
class PerformanceAlert:
    level: str  # 'warning', 'critical'
    metric: str
    value: float
    threshold: float
    message: str

class PerformanceMonitor:
    def __init__(self):
        self.thresholds = {
            'avg_response_time': {'warning': 2.0, 'critical': 5.0},
            'db_connections': {'warning': 80, 'critical': 95},
            'memory_usage_percent': {'warning': 75, 'critical': 90},
            'queue_length': {'warning': 100, 'critical': 500},
        }
    
    def check_performance_metrics(self) -> List[PerformanceAlert]:
        alerts = []
        
        # Vérifier temps de réponse moyen
        avg_response_time = self.get_avg_response_time()
        alerts.extend(self.check_metric('avg_response_time', avg_response_time))
        
        # Vérifier utilisation base de données
        db_connections = self.get_db_connections_count()
        alerts.extend(self.check_metric('db_connections', db_connections))
        
        # Vérifier utilisation mémoire
        memory_usage = self.get_memory_usage_percent()
        alerts.extend(self.check_metric('memory_usage_percent', memory_usage))
        
        # Vérifier longueur des queues Celery
        queue_length = self.get_celery_queue_length()
        alerts.extend(self.check_metric('queue_length', queue_length))
        
        return alerts
    
    def check_metric(self, metric_name: str, value: float) -> List[PerformanceAlert]:
        alerts = []
        thresholds = self.thresholds.get(metric_name, {})
        
        if value >= thresholds.get('critical', float('inf')):
            alerts.append(PerformanceAlert(
                level='critical',
                metric=metric_name,
                value=value,
                threshold=thresholds['critical'],
                message=f"Critical: {metric_name} is {value} (threshold: {thresholds['critical']})"
            ))
        elif value >= thresholds.get('warning', float('inf')):
            alerts.append(PerformanceAlert(
                level='warning',
                metric=metric_name,
                value=value,
                threshold=thresholds['warning'],
                message=f"Warning: {metric_name} is {value} (threshold: {thresholds['warning']})"
            ))
        
        return alerts

# Tâche Celery pour monitoring périodique
@app.task
def performance_monitoring_task():
    monitor = PerformanceMonitor()
    alerts = monitor.check_performance_metrics()
    
    for alert in alerts:
        if alert.level == 'critical':
            # Envoyer notification immédiate
            send_critical_alert(alert)
        else:
            # Logger pour review
            logging.warning(alert.message)
```

## Optimisations infrastructure

### Configuration système

#### Optimisation PostgreSQL
```sql
-- postgresql.conf optimisé pour ETL
# Memory settings
shared_buffers = 2GB                    # 25% of RAM
effective_cache_size = 6GB              # 75% of RAM
work_mem = 256MB                        # For sorting operations
maintenance_work_mem = 1GB              # For VACUUM, CREATE INDEX

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
checkpoint_segments = 32

# Logging
log_min_duration_statement = 1000       # Log slow queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on

# Performance
random_page_cost = 1.1                  # For SSD
effective_io_concurrency = 200          # For SSD
max_worker_processes = 8
max_parallel_workers_per_gather = 4
```

#### Optimisation Redis
```conf
# redis.conf pour Celery
# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511
databases 16

# Logging
loglevel notice
syslog-enabled yes
```

Cette documentation d'optimisation des performances couvre les aspects essentiels pour maintenir une plateforme ETL performante à grande échelle. L'approche est holistique, allant des optimisations base de données aux configurations infrastructure.
