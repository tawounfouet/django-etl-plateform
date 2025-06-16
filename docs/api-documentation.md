# Documentation API - Django ETL Platform

## Vue d'ensemble

Cette documentation couvre l'API REST complète de la plateforme ETL Django. L'API suit les principes REST et utilise Django REST Framework avec authentification JWT.

## Base URL

```
Production: https://api.etl-platform.com/v1/
Staging: https://staging-api.etl-platform.com/v1/
Development: http://localhost:8000/api/v1/
```

## Authentification

### JWT Authentication

```http
POST /auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Réponse:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Utilisation du token

```http
Authorization: Bearer <access_token>
```

### Refresh du token

```http
POST /auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Endpoints principaux

### Organisations

#### Lister les organisations
```http
GET /organizations/
```

**Réponse:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "created_at": "2025-01-15T10:30:00Z",
      "settings": {
        "timezone": "UTC",
        "default_retention_days": 90
      }
    }
  ]
}
```

#### Créer une organisation
```http
POST /organizations/
Content-Type: application/json

{
  "name": "New Organization",
  "settings": {
    "timezone": "Europe/Paris",
    "default_retention_days": 365
  }
}
```

### Connecteurs

#### Lister les connecteurs
```http
GET /connectors/
```

**Paramètres de requête:**
- `connector_type`: Filtrer par type (postgresql, mysql, rest_api, s3)
- `is_active`: Filtrer par statut actif (true/false)
- `search`: Recherche textuelle dans le nom

**Réponse:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Production Database",
      "connector_type": "postgresql",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "config": {
        "host": "prod-db.example.com",
        "port": 5432,
        "database": "production"
      }
    }
  ]
}
```

#### Créer un connecteur
```http
POST /connectors/
Content-Type: application/json

{
  "name": "New PostgreSQL Connector",
  "connector_type": "postgresql",
  "config": {
    "host": "localhost",
    "port": 5432,
    "database": "test_db",
    "schema": "public"
  },
  "credentials": {
    "username": "db_user",
    "password": "secure_password"
  }
}
```

#### Tester un connecteur
```http
POST /connectors/{id}/test/
```

**Réponse:**
```json
{
  "success": true,
  "message": "Connection successful",
  "response_time_ms": 45
}
```

#### Récupérer le schéma
```http
GET /connectors/{id}/schema/
```

**Réponse:**
```json
{
  "tables": ["users", "orders", "products"],
  "columns": {
    "users": ["id", "name", "email", "created_at"],
    "orders": ["id", "user_id", "total", "created_at"]
  },
  "data_types": {
    "users": {
      "id": {"type": "integer", "nullable": false},
      "name": {"type": "varchar", "nullable": false},
      "email": {"type": "varchar", "nullable": true}
    }
  }
}
```

### Pipelines

#### Lister les pipelines
```http
GET /pipelines/
```

**Paramètres de requête:**
- `status`: active, paused, draft, deprecated
- `organization`: ID de l'organisation
- `search`: Recherche dans nom et description
- `ordering`: created_at, -created_at, name, -name

**Réponse:**
```json
{
  "count": 10,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Daily Data Sync",
      "description": "Synchronisation quotidienne des données client",
      "status": "active",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-06-15T14:20:00Z",
      "steps_count": 3,
      "last_run": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "status": "success",
        "started_at": "2025-06-16T02:00:00Z",
        "completed_at": "2025-06-16T02:15:00Z"
      },
      "config": {
        "schedule": "0 2 * * *",
        "timeout": 3600,
        "retry_count": 3
      }
    }
  ]
}
```

#### Créer un pipeline
```http
POST /pipelines/
Content-Type: application/json

{
  "name": "Customer Data Pipeline",
  "description": "Pipeline pour traiter les données clients",
  "config": {
    "schedule": "0 3 * * *",
    "timeout": 1800,
    "retry_count": 2,
    "notifications": {
      "on_success": ["email"],
      "on_failure": ["email", "slack"]
    }
  },
  "steps": [
    {
      "name": "Extract Customer Data",
      "step_type": "extract",
      "order_index": 1,
      "config": {
        "connector_id": "550e8400-e29b-41d4-a716-446655440001",
        "query": "SELECT * FROM customers WHERE updated_at > '{{ last_run_date }}'"
      }
    },
    {
      "name": "Transform Data",
      "step_type": "transform",
      "order_index": 2,
      "config": {
        "transformations": [
          {
            "type": "rename_columns",
            "mapping": {"customer_id": "id", "customer_name": "name"}
          }
        ]
      }
    }
  ]
}
```

#### Exécuter un pipeline
```http
POST /pipelines/{id}/execute/
Content-Type: application/json

{
  "context": {
    "manual_trigger": true,
    "parameters": {
      "start_date": "2025-06-01",
      "end_date": "2025-06-16"
    }
  }
}
```

**Réponse:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440004",
  "status": "pending",
  "message": "Pipeline execution started",
  "estimated_duration": 900
}
```

#### Arrêter un pipeline
```http
POST /pipelines/{id}/stop/
Content-Type: application/json

{
  "run_id": "550e8400-e29b-41d4-a716-446655440004",
  "reason": "Manual stop by user"
}
```

### Exécutions de pipeline

#### Lister les exécutions
```http
GET /pipeline-runs/
```

**Paramètres de requête:**
- `pipeline`: ID du pipeline
- `status`: pending, running, success, failed, cancelled
- `started_at__gte`: Date de début minimum
- `started_at__lte`: Date de début maximum

**Réponse:**
```json
{
  "count": 50,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "pipeline": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Daily Data Sync"
      },
      "status": "success",
      "started_at": "2025-06-16T02:00:00Z",
      "completed_at": "2025-06-16T02:15:00Z",
      "duration": 900,
      "trigger_type": "scheduled",
      "triggered_by": null,
      "context": {
        "schedule_time": "2025-06-16T02:00:00Z"
      },
      "metrics": {
        "total_rows_processed": 15642,
        "success_rate": 1.0,
        "average_processing_time": 0.057
      }
    }
  ]
}
```

#### Détails d'une exécution
```http
GET /pipeline-runs/{id}/
```

**Réponse complète avec détails des tâches:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "pipeline": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Daily Data Sync"
  },
  "status": "success",
  "started_at": "2025-06-16T02:00:00Z",
  "completed_at": "2025-06-16T02:15:00Z",
  "task_runs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "step_name": "Extract Customer Data",
      "status": "success",
      "started_at": "2025-06-16T02:00:30Z",
      "completed_at": "2025-06-16T02:05:00Z",
      "metrics": {
        "rows_extracted": 15642,
        "extraction_rate": 58.2
      }
    }
  ]
}
```

#### Logs d'une exécution
```http
GET /pipeline-runs/{id}/logs/
```

**Paramètres de requête:**
- `level`: INFO, WARNING, ERROR
- `limit`: Nombre maximum de logs à retourner
- `offset`: Décalage pour pagination

**Réponse:**
```json
{
  "count": 245,
  "results": [
    {
      "timestamp": "2025-06-16T02:00:30.123Z",
      "level": "INFO",
      "message": "Starting data extraction from PostgreSQL",
      "task_id": "550e8400-e29b-41d4-a716-446655440005",
      "context": {
        "connector_type": "postgresql",
        "query": "SELECT * FROM customers..."
      }
    }
  ]
}
```

### Alertes

#### Lister les alertes
```http
GET /alerts/
```

**Paramètres de requête:**
- `level`: info, warning, error, critical
- `is_resolved`: true/false
- `created_at__gte`: Date de création minimum

**Réponse:**
```json
{
  "count": 15,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "level": "error",
      "alert_type": "pipeline_failed",
      "message": "Pipeline 'Daily Data Sync' failed due to connection timeout",
      "pipeline_run": "550e8400-e29b-41d4-a716-446655440004",
      "is_resolved": false,
      "created_at": "2025-06-16T02:15:30Z",
      "metadata": {
        "error_code": "CONNECTION_TIMEOUT",
        "retry_count": 3
      }
    }
  ]
}
```

#### Résoudre une alerte
```http
PATCH /alerts/{id}/
Content-Type: application/json

{
  "is_resolved": true,
  "resolution_note": "Connection issue fixed by restarting database service"
}
```

### Métriques

#### Métriques système
```http
GET /metrics/system/
```

**Réponse:**
```json
{
  "active_pipelines": 12,
  "running_executions": 3,
  "queued_tasks": 45,
  "success_rate_24h": 0.97,
  "average_execution_time": 450,
  "total_data_processed_today": 2450000
}
```

#### Métriques d'un pipeline
```http
GET /metrics/pipelines/{id}/
```

**Paramètres de requête:**
- `period`: 1h, 24h, 7d, 30d
- `granularity`: minute, hour, day

**Réponse:**
```json
{
  "pipeline_id": "550e8400-e29b-41d4-a716-446655440002",
  "period": "7d",
  "metrics": {
    "total_executions": 14,
    "successful_executions": 13,
    "failed_executions": 1,
    "success_rate": 0.93,
    "average_duration": 875,
    "median_duration": 820,
    "p95_duration": 1200,
    "total_rows_processed": 218984,
    "average_throughput": 250.6
  },
  "timeline": [
    {
      "timestamp": "2025-06-09T00:00:00Z",
      "executions": 2,
      "success_rate": 1.0,
      "avg_duration": 860
    }
  ]
}
```

## Codes d'erreur

### Codes HTTP standards
- `200 OK`: Succès
- `201 Created`: Ressource créée
- `400 Bad Request`: Erreur dans la requête
- `401 Unauthorized`: Non authentifié
- `403 Forbidden`: Non autorisé
- `404 Not Found`: Ressource non trouvée
- `500 Internal Server Error`: Erreur serveur

### Codes d'erreur métier

```json
{
  "error": {
    "code": "PIPELINE_VALIDATION_ERROR",
    "message": "Pipeline configuration is invalid",
    "details": {
      "field": "config.schedule",
      "issue": "Invalid cron expression"
    }
  }
}
```

**Codes d'erreur principaux:**
- `CONNECTOR_CONNECTION_FAILED`: Échec de connexion
- `PIPELINE_VALIDATION_ERROR`: Erreur de validation
- `PIPELINE_EXECUTION_FAILED`: Échec d'exécution
- `INSUFFICIENT_PERMISSIONS`: Permissions insuffisantes
- `RESOURCE_NOT_FOUND`: Ressource introuvable
- `RATE_LIMIT_EXCEEDED`: Limite de taux dépassée

## Pagination

Les endpoints de liste utilisent la pagination par curseur :

```json
{
  "count": 100,
  "next": "http://api.example.com/pipelines/?cursor=cD0yMDIzLTA2LTE2",
  "previous": null,
  "results": [...]
}
```

## Filtrage et recherche

### Opérateurs de filtre
- `field__gt`: Supérieur à
- `field__gte`: Supérieur ou égal
- `field__lt`: Inférieur à
- `field__lte`: Inférieur ou égal
- `field__in`: Dans la liste
- `field__icontains`: Contient (insensible à la casse)

### Exemple
```http
GET /pipeline-runs/?status__in=success,failed&started_at__gte=2025-06-01&search=customer
```

## Rate Limiting

L'API applique des limites de taux :
- **Authentifié**: 1000 requêtes/heure
- **Non authentifié**: 100 requêtes/heure
- **Webhooks**: 10000 requêtes/heure

Headers de réponse :
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1640995200
```

## WebSocket API

### Connexion temps réel aux exécutions

```javascript
const ws = new WebSocket('wss://api.etl-platform.com/ws/pipeline-runs/550e8400-e29b-41d4-a716-446655440004/');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Pipeline status update:', data);
};

// Messages reçus
{
  "type": "status_update",
  "data": {
    "run_id": "550e8400-e29b-41d4-a716-446655440004",
    "status": "running",
    "progress": 0.45,
    "current_step": "Transform Data"
  }
}
```

## SDKs et bibliothèques

### Python SDK

```python
from etl_platform_sdk import ETLPlatformClient

client = ETLPlatformClient(
    base_url='https://api.etl-platform.com/v1/',
    token='your_jwt_token'
)

# Lister les pipelines
pipelines = client.pipelines.list()

# Exécuter un pipeline
run = client.pipelines.execute(
    pipeline_id='550e8400-e29b-41d4-a716-446655440002',
    context={'manual_trigger': True}
)

# Surveiller l'exécution
for update in client.pipeline_runs.stream(run.id):
    print(f"Status: {update.status}, Progress: {update.progress}")
```

### JavaScript SDK

```javascript
import { ETLPlatformClient } from '@etl-platform/sdk';

const client = new ETLPlatformClient({
  baseURL: 'https://api.etl-platform.com/v1/',
  token: 'your_jwt_token'
});

// Exécuter un pipeline
const run = await client.pipelines.execute(pipelineId, {
  context: { manual_trigger: true }
});

// Écouter les mises à jour
client.pipelineRuns.subscribe(run.id, (update) => {
  console.log('Status update:', update);
});
```

## Exemples d'intégration

### Webhook pour notifications

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/etl-notifications', methods=['POST'])
def handle_etl_webhook():
    # Vérifier la signature
    signature = request.headers.get('X-ETL-Signature')
    body = request.get_data()
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return 'Invalid signature', 401
    
    # Traiter l'événement
    event = request.json
    if event['type'] == 'pipeline.execution.completed':
        handle_pipeline_completion(event['data'])
    
    return 'OK', 200
```

Cette documentation API complète permet aux développeurs d'intégrer facilement la plateforme ETL dans leurs applications et workflows.
