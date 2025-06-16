# Guide de Déploiement - Django ETL Platform

## Vue d'ensemble

Ce guide couvre le déploiement de la plateforme ETL Django dans différents environnements, des installations locales aux déploiements en production avec Kubernetes.

## Architecture de déploiement

### Environnements

```mermaid
graph TD
    A[Development] --> B[Staging]
    B --> C[Production]
    
    A --> D[Local Docker]
    B --> E[Docker Compose]
    C --> F[Kubernetes]
    
    D --> G[SQLite/PostgreSQL]
    E --> H[PostgreSQL + Redis]
    F --> I[PostgreSQL Cluster + Redis Cluster]
```

## Déploiement local avec Docker

### Docker Compose pour développement

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: etl_platform_dev
      POSTGRES_USER: etl_user
      POSTGRES_PASSWORD: etl_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  django:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    environment:
      - DJANGO_SETTINGS_MODULE=etl_platform.settings.development
      - DATABASE_URL=postgresql://etl_user:etl_password@postgres:5432/etl_platform_dev
      - CELERY_BROKER_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - media_files:/app/media
    depends_on:
      - postgres
      - redis
    command: python manage.py runserver 0.0.0.0:8000

  celery-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    environment:
      - DJANGO_SETTINGS_MODULE=etl_platform.settings.development
      - DATABASE_URL=postgresql://etl_user:etl_password@postgres:5432/etl_platform_dev
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
    command: celery -A etl_platform worker --loglevel=info

  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    environment:
      - DJANGO_SETTINGS_MODULE=etl_platform.settings.development
      - DATABASE_URL=postgresql://etl_user:etl_password@postgres:5432/etl_platform_dev
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis
    command: celery -A etl_platform beat --loglevel=info

volumes:
  postgres_data:
  redis_data:
  media_files:
```

### Dockerfile optimisé

```dockerfile
# docker/Dockerfile.prod
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements/production.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/production.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy application code
COPY . /app/
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "etl_platform.wsgi:application"]
```

## Déploiement avec Kubernetes

### Namespace et ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: etl-platform
  labels:
    name: etl-platform

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: etl-platform-config
  namespace: etl-platform
data:
  DJANGO_SETTINGS_MODULE: "etl_platform.settings.production"
  CELERY_BROKER_URL: "redis://redis-service:6379/0"
  CELERY_RESULT_BACKEND: "redis://redis-service:6379/1"
  PROMETHEUS_ENABLED: "true"
  LOG_LEVEL: "INFO"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: etl-platform-secrets
  namespace: etl-platform
type: Opaque
data:
  # Base64 encoded values
  SECRET_KEY: <base64-encoded-secret-key>
  DATABASE_URL: <base64-encoded-database-url>
  ENCRYPTION_KEY: <base64-encoded-encryption-key>
  SENTRY_DSN: <base64-encoded-sentry-dsn>
```

### PostgreSQL avec persistance

```yaml
# k8s/postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: etl-platform
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: etl-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: etl_platform
        - name: POSTGRES_USER
          value: etl_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: etl-platform
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Redis cluster

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: etl-platform
spec:
  serviceName: redis-service
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
          - redis-server
          - --appendonly
          - "yes"
          - --cluster-enabled
          - "yes"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: etl-platform
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
```

### Application Django

```yaml
# k8s/django-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-app
  namespace: etl-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: django-app
  template:
    metadata:
      labels:
        app: django-app
    spec:
      initContainers:
      - name: migrate
        image: your-registry/etl-platform:latest
        command: ['python', 'manage.py', 'migrate']
        envFrom:
        - configMapRef:
            name: etl-platform-config
        - secretRef:
            name: etl-platform-secrets
      containers:
      - name: django
        image: your-registry/etl-platform:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: etl-platform-config
        - secretRef:
            name: etl-platform-secrets
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: django-service
  namespace: etl-platform
spec:
  selector:
    app: django-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Celery Workers

```yaml
# k8s/celery-workers.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: etl-platform
spec:
  replicas: 5
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: your-registry/etl-platform:latest
        command: ['celery', '-A', 'etl_platform', 'worker', '--loglevel=info', '--concurrency=4']
        envFrom:
        - configMapRef:
            name: etl-platform-config
        - secretRef:
            name: etl-platform-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - celery
            - -A
            - etl_platform
            - inspect
            - ping
          initialDelaySeconds: 30
          periodSeconds: 60

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
  namespace: etl-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
      - name: celery-beat
        image: your-registry/etl-platform:latest
        command: ['celery', '-A', 'etl_platform', 'beat', '--loglevel=info']
        envFrom:
        - configMapRef:
            name: etl-platform-config
        - secretRef:
            name: etl-platform-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

### Ingress avec SSL

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: etl-platform-ingress
  namespace: etl-platform
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/client-max-body-size: "100m"
spec:
  tls:
  - hosts:
    - etl.yourdomain.com
    secretName: etl-platform-tls
  rules:
  - host: etl.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: django-service
            port:
              number: 80
```

## Monitoring et observabilité

### Prometheus et Grafana

```yaml
# k8s/monitoring.yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: etl-platform-metrics
  namespace: etl-platform
spec:
  selector:
    matchLabels:
      app: django-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  etl-platform.json: |
    {
      "dashboard": {
        "title": "ETL Platform Metrics",
        "panels": [
          {
            "title": "Pipeline Execution Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(pipeline_executions_total[5m])"
              }
            ]
          }
        ]
      }
    }
```

### Logging avec ELK Stack

```yaml
# k8s/logging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: etl-platform
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*etl-platform*.log
      processors:
        - add_kubernetes_metadata:
            in_cluster: true
    
    output.elasticsearch:
      hosts: ["elasticsearch:9200"]
      index: "etl-platform-%{+yyyy.MM.dd}"
    
    setup.template.name: "etl-platform"
    setup.template.pattern: "etl-platform-*"
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements/test.txt
    
    - name: Run tests
      run: |
        python manage.py test
        
    - name: Run security checks
      run: |
        bandit -r apps/
        safety check

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -f docker/Dockerfile.prod -t etl-platform:${{ github.sha }} .
        
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker tag etl-platform:${{ github.sha }} your-registry/etl-platform:${{ github.sha }}
        docker push your-registry/etl-platform:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        echo ${{ secrets.KUBE_CONFIG }} | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        
        # Update image tag
        sed -i "s|your-registry/etl-platform:latest|your-registry/etl-platform:${{ github.sha }}|g" k8s/django-app.yaml
        
        # Apply manifests
        kubectl apply -f k8s/
        
        # Wait for rollout
        kubectl rollout status deployment/django-app -n etl-platform
```

## Sécurité en production

### Network Policies

```yaml
# k8s/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: etl-platform-network-policy
  namespace: etl-platform
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - podSelector:
        matchLabels:
          app: django-app
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### Pod Security Standards

```yaml
# k8s/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: etl-platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Scaling et optimisation

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: django-app-hpa
  namespace: etl-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: django-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaler

```yaml
# k8s/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: celery-worker-vpa
  namespace: etl-platform
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: celery-worker
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 256Mi
```

## Backup et recovery

### Database backup

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: etl-platform
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15-alpine
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL | gzip > /backup/backup-$(date +%Y%m%d_%H%M%S).sql.gz
              # Upload to S3 or other storage
              aws s3 cp /backup/backup-$(date +%Y%m%d_%H%M%S).sql.gz s3://your-backup-bucket/
            envFrom:
            - secretRef:
                name: etl-platform-secrets
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir: {}
          restartPolicy: OnFailure
```

## Troubleshooting

### Debug tools

```bash
# Vérifier l'état des pods
kubectl get pods -n etl-platform

# Logs d'un pod
kubectl logs -f deployment/django-app -n etl-platform

# Exécuter des commandes dans un pod
kubectl exec -it deployment/django-app -n etl-platform -- python manage.py shell

# Port forwarding pour debug local
kubectl port-forward svc/django-service 8000:80 -n etl-platform

# Vérifier les métriques
kubectl top pods -n etl-platform
```

### Health checks

```python
# Health check endpoint
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Test database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test Redis
        from django.core.cache import cache
        cache.get('health_check_key')
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```
