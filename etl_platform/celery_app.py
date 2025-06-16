"""
Celery configuration for etl_platform project.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etl_platform.settings.development')

app = Celery('etl_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery task routes
app.conf.task_routes = {
    'apps.tasks.extract.*': {'queue': 'extract'},
    'apps.tasks.transform.*': {'queue': 'transform'},
    'apps.tasks.load.*': {'queue': 'load'},
    'apps.execution.*': {'queue': 'execution'},
    'apps.monitoring.*': {'queue': 'monitoring'},
}

# Celery beat schedule
app.conf.beat_schedule = {
    'cleanup-old-logs': {
        'task': 'apps.monitoring.tasks.cleanup_old_logs',
        'schedule': 3600.0,  # Run every hour
    },
    'health-check': {
        'task': 'apps.monitoring.tasks.health_check',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'update-pipeline-metrics': {
        'task': 'apps.monitoring.tasks.update_pipeline_metrics',
        'schedule': 600.0,  # Run every 10 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
