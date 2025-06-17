"""
Factories pour les modèles de monitoring
"""
import factory
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from apps.monitoring.models import (
    Alert, Metric, HealthCheck, PerformanceReport,
    NotificationChannel, NotificationRule, NotificationLog,
    AlertLevel, AlertType, MetricType
)
from .execution_factories import PipelineRunFactory, TaskRunFactory
from .pipelines_factories import PipelineFactory
from .core_factories import OrganizationFactory
from .authentication_factories import CustomUserFactory

fake = Faker('fr_FR')


class AlertFactory(factory.django.DjangoModelFactory):
    """Factory pour Alert"""
    
    class Meta:
        model = Alert

    id = factory.Faker('uuid4')
    pipeline_run = factory.SubFactory(PipelineRunFactory)
    task_run = factory.SubFactory(TaskRunFactory)
    level = factory.Faker('random_element', elements=[
        AlertLevel.INFO,
        AlertLevel.WARNING,
        AlertLevel.ERROR,
        AlertLevel.CRITICAL,
    ])
    alert_type = factory.Faker('random_element', elements=[
        AlertType.TASK_FAILED,
        AlertType.PIPELINE_FAILED,
        AlertType.PERFORMANCE_DEGRADATION,
        AlertType.RESOURCE_EXHAUSTION,
        AlertType.DATA_QUALITY,
        AlertType.TIMEOUT,
        AlertType.CONNECTION_ERROR,
        AlertType.DISK_SPACE,
        AlertType.MEMORY_USAGE,
    ])
    is_resolved = factory.Faker('boolean', chance_of_getting_true=60)
    resolved_by = factory.Maybe(
        'is_resolved',
        yes_declaration=factory.SubFactory(CustomUserFactory),
        no_declaration=None
    )
    
    @factory.lazy_attribute
    def resolved_at(self):
        if self.is_resolved:
            # Use current time as base since created_at is auto-generated
            base_time = timezone.now()
            return base_time + timedelta(
                hours=fake.random_int(1, 24),
                minutes=fake.random_int(0, 59)
            )
        return None
    
    @factory.lazy_attribute
    def title(self):
        alert_titles = {
            AlertType.TASK_FAILED: f"Tâche {fake.word()} échouée",
            AlertType.PIPELINE_FAILED: f"Pipeline {fake.word()} en erreur",
            AlertType.PERFORMANCE_DEGRADATION: "Dégradation des performances détectée",
            AlertType.RESOURCE_EXHAUSTION: "Ressources système épuisées",
            AlertType.DATA_QUALITY: "Problème de qualité des données",
            AlertType.TIMEOUT: "Timeout d'exécution dépassé",
            AlertType.CONNECTION_ERROR: "Erreur de connexion",
            AlertType.DISK_SPACE: "Espace disque insuffisant",
            AlertType.MEMORY_USAGE: "Utilisation mémoire critique",
        }
        return alert_titles.get(self.alert_type, "Alerte système")
    
    @factory.lazy_attribute
    def message(self):
        messages = {
            AlertType.TASK_FAILED: f"La tâche '{fake.word()}' a échoué avec l'erreur: {fake.sentence()}",
            AlertType.PIPELINE_FAILED: f"Le pipeline '{fake.word()}' s'est arrêté de façon inattendue",
            AlertType.PERFORMANCE_DEGRADATION: f"Les performances ont chuté de {fake.random_int(20, 60)}% par rapport à la moyenne",
            AlertType.RESOURCE_EXHAUSTION: f"Utilisation CPU: {fake.random_int(85, 99)}%, Mémoire: {fake.random_int(80, 95)}%",
            AlertType.DATA_QUALITY: f"Détection de {fake.random_int(50, 500)} enregistrements invalides",
            AlertType.TIMEOUT: f"Timeout de {fake.random_int(60, 600)} secondes dépassé",
            AlertType.CONNECTION_ERROR: f"Impossible de se connecter à {fake.domain_name()}",
            AlertType.DISK_SPACE: f"Espace disque restant: {fake.random_int(1, 10)}%",
            AlertType.MEMORY_USAGE: f"Utilisation mémoire: {fake.random_int(85, 99)}%",
        }
        return messages.get(self.alert_type, fake.text(max_nb_chars=200))
    
    metadata = factory.LazyAttribute(lambda obj: _generate_alert_metadata(obj.alert_type))


def _generate_alert_metadata(alert_type):
    """Génère des métadonnées spécifiques selon le type d'alerte"""
    base_metadata = {
        'server': fake.domain_name(),
        'timestamp': fake.date_time().isoformat(),
        'environment': fake.random_element(['dev', 'staging', 'prod']),
    }
    
    if alert_type == AlertType.PERFORMANCE_DEGRADATION:
        base_metadata.update({
            'baseline_duration': fake.random_int(300, 1800),
            'current_duration': fake.random_int(600, 3600),
            'degradation_percent': fake.random_int(20, 80),
            'affected_components': fake.words(nb=fake.random_int(1, 3))
        })
    elif alert_type == AlertType.RESOURCE_EXHAUSTION:
        base_metadata.update({
            'cpu_usage': fake.random_int(80, 99),
            'memory_usage': fake.random_int(75, 95),
            'disk_usage': fake.random_int(70, 90),
            'processes': fake.random_int(50, 200)
        })
    elif alert_type == AlertType.DATA_QUALITY:
        base_metadata.update({
            'invalid_records': fake.random_int(10, 1000),
            'total_records': fake.random_int(10000, 100000),
            'error_types': fake.random_elements([
                'null_values', 'format_error', 'range_violation', 'duplicate'
            ], length=fake.random_int(1, 3)),
            'affected_columns': fake.words(nb=fake.random_int(1, 5))
        })
    
    return base_metadata


class MetricFactory(factory.django.DjangoModelFactory):
    """Factory pour Metric"""
    
    class Meta:
        model = Metric

    id = factory.Faker('uuid4')
    name = factory.Faker('random_element', elements=[
        'pipeline.execution_time',
        'pipeline.records_processed',
        'pipeline.success_rate',
        'system.cpu_usage',
        'system.memory_usage',
        'system.disk_usage',
        'task.duration',
        'task.throughput',
        'data.quality_score',
        'api.response_time',
    ])
    metric_type = factory.Faker('random_element', elements=[
        MetricType.COUNTER,
        MetricType.GAUGE,
        MetricType.HISTOGRAM,
        MetricType.TIMING,
    ])
    pipeline_run = factory.SubFactory(PipelineRunFactory)
    task_run = factory.SubFactory(TaskRunFactory)
    
    @factory.lazy_attribute
    def value(self):
        metric_ranges = {
            'pipeline.execution_time': (60, 7200),
            'pipeline.records_processed': (1000, 1000000),
            'pipeline.success_rate': (0.8, 1.0),
            'system.cpu_usage': (10, 95),
            'system.memory_usage': (20, 90),
            'system.disk_usage': (30, 80),
            'task.duration': (10, 1800),
            'task.throughput': (100, 10000),
            'data.quality_score': (0.7, 1.0),
            'api.response_time': (50, 2000),
        }
        
        min_val, max_val = metric_ranges.get(self.name, (0, 100))
        if isinstance(min_val, float):
            return fake.random.uniform(min_val, max_val)
        return fake.random_int(min_val, max_val)
    
    tags = factory.LazyFunction(lambda: {
        'environment': fake.random_element(['dev', 'staging', 'prod']),
        'region': fake.random_element(['us-east-1', 'eu-west-1', 'ap-southeast-1']),
        'team': fake.random_element(['data', 'analytics', 'engineering']),
        'priority': fake.random_element(['low', 'medium', 'high']),
        'component': fake.random_element(['extract', 'transform', 'load', 'monitor']),
    })


class HealthCheckFactory(factory.django.DjangoModelFactory):
    """Factory pour HealthCheck"""
    
    class Meta:
        model = HealthCheck

    id = factory.Faker('uuid4')
    component = factory.Faker('random_element', elements=[
        'database', 'redis', 'celery', 'api', 'storage',
        'etl_engine', 'monitoring', 'scheduler', 'notification'
    ])
    status = factory.Faker('random_element', elements=[
        'healthy', 'degraded', 'unhealthy'
    ])
    response_time_ms = factory.Faker('random_int', min=1, max=5000)
    
    @factory.lazy_attribute
    def details(self):
        details_by_component = {
            'database': {
                'connection_pool_size': fake.random_int(10, 100),
                'active_connections': fake.random_int(5, 50),
                'query_avg_time_ms': fake.random_int(10, 500),
            },
            'redis': {
                'memory_usage_mb': fake.random_int(100, 2048),
                'keyspace_hits': fake.random_int(1000, 100000),
                'keyspace_misses': fake.random_int(100, 10000),
            },
            'api': {
                'requests_per_minute': fake.random_int(10, 1000),
                'error_rate': fake.random.uniform(0, 0.1),
                'avg_response_time': fake.random_int(50, 2000),
            },
            'storage': {
                'free_space_gb': fake.random_int(10, 1000),
                'total_space_gb': fake.random_int(100, 10000),
                'io_wait_percent': fake.random_int(0, 30),
            }
        }
        return details_by_component.get(self.component, {})
    
    @factory.lazy_attribute
    def error_message(self):
        if self.status == 'unhealthy':
            error_messages = {
                'database': "Connection timeout exceeded",
                'redis': "Memory usage critical",
                'api': "High error rate detected",
                'storage': "Disk space critically low"
            }
            return error_messages.get(self.component, "Component check failed")
        return ""


class PerformanceReportFactory(factory.django.DjangoModelFactory):
    """Factory pour PerformanceReport"""
    
    class Meta:
        model = PerformanceReport

    id = factory.Faker('uuid4')
    pipeline = factory.SubFactory(PipelineFactory)
    report_date = factory.Faker('date_this_month')
    total_runs = factory.Faker('random_int', min=1, max=100)
    
    @factory.lazy_attribute
    def successful_runs(self):
        return fake.random_int(int(self.total_runs * 0.6), self.total_runs)
    
    @factory.lazy_attribute
    def failed_runs(self):
        return self.total_runs - self.successful_runs
    
    avg_duration_seconds = factory.Faker('random_int', min=300, max=3600)
    min_duration_seconds = factory.LazyAttribute(lambda obj: fake.random_int(60, int(obj.avg_duration_seconds * 0.5)))
    max_duration_seconds = factory.LazyAttribute(lambda obj: fake.random_int(int(obj.avg_duration_seconds * 1.5), obj.avg_duration_seconds * 3))
    data_processed_bytes = factory.Faker('random_int', min=1000000, max=10000000000)  # 1MB à 10GB
    cpu_usage_avg = factory.Faker('random_int', min=20, max=80)
    memory_usage_avg = factory.Faker('random_int', min=30, max=70)
    
    recommendations = factory.LazyFunction(lambda: [
        fake.random_element([
            "Optimiser les requêtes SQL pour réduire le temps d'exécution",
            "Augmenter la taille des lots pour améliorer le débit",
            "Ajouter des index sur les colonnes de jointure",
            "Considérer l'exécution en parallèle pour les grandes données",
            "Implémenter la mise en cache pour réduire les accès répétés",
            "Revoir la stratégie de partitionnement des données",
            "Optimiser l'allocation mémoire des tâches",
            "Planifier l'exécution pendant les heures creuses"
        ]) for _ in range(fake.random_int(1, 3))
    ])


class NotificationChannelFactory(factory.django.DjangoModelFactory):
    """Factory pour NotificationChannel"""
    
    class Meta:
        model = NotificationChannel

    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    channel_type = factory.Faker('random_element', elements=[
        'email', 'slack', 'webhook', 'sms', 'teams'
    ])
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(CustomUserFactory)
    is_active = factory.Faker('boolean', chance_of_getting_true=85)
    
    @factory.lazy_attribute
    def config(self):
        config_by_type = {
            'email': {
                'smtp_server': fake.domain_name(),
                'smtp_port': 587,
                'username': fake.email(),
                'use_tls': True,
                'from_email': fake.email(),
            },
            'slack': {
                'webhook_url': f"https://hooks.slack.com/services/{fake.uuid4()}",
                'channel': f"#{fake.word()}",
                'username': 'ETL Platform',
            },
            'webhook': {
                'url': fake.url(),
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {fake.sha256()}"
                },
                'timeout_seconds': 30,
            },
            'sms': {
                'provider': fake.random_element(['twilio', 'nexmo', 'aws_sns']),
                'api_key': fake.sha256(),
                'from_number': fake.phone_number(),
            },
            'teams': {
                'webhook_url': f"https://outlook.office.com/webhook/{fake.uuid4()}",
                'card_format': True,
            }
        }
        return config_by_type.get(self.channel_type, {})


class NotificationRuleFactory(factory.django.DjangoModelFactory):
    """Factory pour NotificationRule"""
    
    class Meta:
        model = NotificationRule

    id = factory.Faker('uuid4')
    name = factory.Faker('sentence', nb_words=3)
    organization = factory.SubFactory(OrganizationFactory)
    
    # Note: Les autres champs seraient définis selon le modèle complet


class NotificationLogFactory(factory.django.DjangoModelFactory):
    """Factory pour NotificationLog"""
    
    class Meta:
        model = NotificationLog

    # Note: Les champs seraient définis selon le modèle complet
    pass


# Factories spécialisées pour différents types d'alertes

class CriticalAlertFactory(AlertFactory):
    """Factory pour alertes critiques"""
    level = AlertLevel.CRITICAL
    alert_type = factory.Faker('random_element', elements=[
        AlertType.PIPELINE_FAILED,
        AlertType.RESOURCE_EXHAUSTION,
        AlertType.CONNECTION_ERROR,
    ])
    is_resolved = False


class PerformanceAlertFactory(AlertFactory):
    """Factory pour alertes de performance"""
    level = AlertLevel.WARNING
    alert_type = AlertType.PERFORMANCE_DEGRADATION
    
    metadata = factory.LazyFunction(lambda: {
        'baseline_duration': fake.random_int(300, 1800),
        'current_duration': fake.random_int(600, 3600),
        'degradation_percent': fake.random_int(30, 80),
        'threshold_exceeded': True,
        'trend': 'increasing',
        'impact_assessment': fake.random_element(['low', 'medium', 'high'])
    })


class DataQualityAlertFactory(AlertFactory):
    """Factory pour alertes de qualité des données"""
    level = AlertLevel.ERROR
    alert_type = AlertType.DATA_QUALITY
    
    metadata = factory.LazyFunction(lambda: {
        'invalid_records': fake.random_int(10, 1000),
        'total_records': fake.random_int(10000, 100000),
        'quality_score': fake.random.uniform(0.3, 0.7),
        'rules_violated': fake.random_elements([
            'not_null', 'unique', 'range_check', 'format_check'
        ], length=fake.random_int(1, 3)),
        'affected_tables': fake.words(nb=fake.random_int(1, 3))
    })


# Factory pour créer un tableau de bord de monitoring complet

class MonitoringDashboardFactory:
    """Factory pour créer un ensemble complet de données de monitoring"""
    
    @classmethod
    def create_dashboard_data(cls, organization=None, days=7):
        """Crée des données complètes pour un tableau de bord de monitoring"""
        if not organization:
            organization = OrganizationFactory()
        
        # Créer des alertes récentes
        alerts = []
        for _ in range(fake.random_int(5, 20)):
            alert = AlertFactory()
            alerts.append(alert)
        
        # Créer des métriques système
        metrics = []
        current_time = timezone.now()
        for hour in range(days * 24):
            timestamp = current_time - timedelta(hours=hour)
            
            # Métriques système
            for metric_name in ['system.cpu_usage', 'system.memory_usage', 'system.disk_usage']:
                metric = MetricFactory(
                    name=metric_name,
                    timestamp=timestamp,
                    pipeline_run=None,
                    task_run=None
                )
                metrics.append(metric)
        
        # Créer des health checks
        health_checks = []
        for component in ['database', 'redis', 'api', 'storage', 'scheduler']:
            health_check = HealthCheckFactory(component=component)
            health_checks.append(health_check)
        
        # Créer des rapports de performance
        performance_reports = []
        for pipeline in organization.pipelines.all()[:5]:  # Top 5 pipelines
            report = PerformanceReportFactory(pipeline=pipeline)
            performance_reports.append(report)
        
        return {
            'alerts': alerts,
            'metrics': metrics,
            'health_checks': health_checks,
            'performance_reports': performance_reports,
        }
