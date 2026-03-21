# 🚀 DEPLOYMENT.md - Cloud Setup & Production Deployment

**Date**: March 20, 2026  
**Purpose**: Complete guide for deploying CV Intelligence Platform to production  
**Target Audience**: DevOps engineers, system administrators  

---

## 🎯 Deployment Overview

This guide covers three deployment scenarios:

1. **Local Development** (CLI & Dashboard)
2. **Docker Containerized** (Single container or compose)
3. **Cloud Production** (AWS, GCP, Azure)

### Architecture
```
┌─────────────────────────────────────────────┐
│        User (Web Browser)                   │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│    Streamlit Dashboard (Port 8501)           │
│    - File Upload                             │
│    - Search & Filter                         │
│    - Job Scoring                             │
│    - CSV Export                              │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│    FastAPI Backend (Port 8000)               │
│    - /api/search                             │
│    - /api/score                              │
│    - /api/extract                            │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│    Data & Models                             │
│    - FAISS Index (vector search)             │
│    - CSV Data (candidates)                   │
│    - spaCy Model (NER)                       │
│    - sentence-transformer (embeddings)       │
└─────────────────────────────────────────────┘
```

---

## Part 1: Local Development Setup

### Prerequisites
```bash
Linux/macOS:
- Python 3.10+
- Virtual environment
- Git

Windows:
- Python 3.10+ (from python.org)
- Visual C++ Build Tools
- Git
```

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd cv-filtering

# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r demo/requirements.txt
```

### Running Locally

```bash
# Terminal 1: Start FastAPI backend
cd demo
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit dashboard
streamlit run src/dashboard/app.py --server.port=8501

# Access at:
# - Dashboard: http://localhost:8501
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Configuration

Create `.env` file in project root:

```bash
# demo/.env
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
MODEL_CACHE_DIR=/tmp/models
EMBEDDING_BATCH_SIZE=64
FAISS_INDEX_TYPE=IndexFlatL2
```

---

## Part 2: Docker Containerization

### Single Container (Development)

**File**: `Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY demo/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY demo/ .

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run both services
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 & streamlit run src/dashboard/app.py --server.port=8501 --server.headless true"]
```

### Docker Compose (Production)

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - MODEL_CACHE_DIR=/models
    volumes:
      - ./demo/data:/app/data:ro
      - model_cache:/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - cv_network

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8501:8501"
    environment:
      - PYTHONUNBUFFERED=1
      - API_URL=http://api:8000
    depends_on:
      - api
    volumes:
      - ./demo/data:/app/data:ro
    networks:
      - cv_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - dashboard
    networks:
      - cv_network

volumes:
  model_cache:

networks:
  cv_network:
    driver: bridge
```

### Build and Run

```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Networking

```bash
# API accessible internally as: http://api:8000
# Dashboard accessible at: http://localhost:8501
# Nginx proxy at: http://localhost:80
```

---

## Part 3: Cloud Deployment

### AWS Deployment (ECS + ALB)

#### 1. Create ECR Registry

```bash
# Set variables
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPOSITORY_NAME=cv-intelligence

# Create registry
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

#### 2. Push Images

```bash
# Build and tag
docker build -t cv-api:latest -f Dockerfile.api .
docker build -t cv-dashboard:latest -f Dockerfile.dashboard .

# Tag for ECR
docker tag cv-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:api-latest
docker tag cv-dashboard:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:dashboard-latest

# Push
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:api-latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:dashboard-latest
```

#### 3. Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name cv-cluster --region $REGION

# Create task definitions (use JSON below)
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION
```

**File**: `task-definition.json`

```json
{
  "family": "cv-intelligence",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/cv-intelligence:api-latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "MODEL_CACHE_DIR", "value": "/models"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cv-intelligence",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    },
    {
      "name": "dashboard",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/cv-intelligence:dashboard-latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "hostPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_URL", "value": "http://api:8000"}
      ],
      "dependsOn": [
        {
          "containerName": "api",
          "condition": "START"
        }
      ]
    }
  ]
}
```

#### 4. Create Service

```bash
# Create Application Load Balancer (ALB)
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name cv-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --scheme internet-facing \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create target groups
API_TG=$(aws elbv2 create-target-group \
  --name cv-api-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

DASHBOARD_TG=$(aws elbv2 create-target-group \
  --name cv-dashboard-tg \
  --protocol HTTP \
  --port 8501 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create ECS service
aws ecs create-service \
  --cluster cv-cluster \
  --service-name cv-service \
  --task-definition cv-intelligence:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration='{subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}' \
  --load-balancers targetGroupArn=$API_TG,containerName=api,containerPort=8000 \
  --region $REGION
```

### Google Cloud Deployment (Cloud Run)

```bash
# Set project
PROJECT_ID=my-project
gcloud config set project $PROJECT_ID

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/cv-api:latest .

# Deploy to Cloud Run
gcloud run deploy cv-api \
  --image gcr.io/$PROJECT_ID/cv-api:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --port 8000 \
  --set-env-vars "LOG_LEVEL=INFO"

gcloud run deploy cv-dashboard \
  --image gcr.io/$PROJECT_ID/cv-dashboard:latest \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --port 8501 \
  --set-env-vars "API_URL=https://cv-api-xxxxx.a.run.app"
```

### Azure Container Instances

```bash
# Set variables
RESOURCE_GROUP=cv-rg
REGISTRY_NAME=cvintelligence
LOCATION=eastus

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
az acr create --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME --sku Basic

# Build and push
az acr build --registry $REGISTRY_NAME --image cv-api:latest .

# Deploy container instances
az container create --resource-group $RESOURCE_GROUP \
  --name cv-api-container \
  --image $REGISTRY_NAME.azurecr.io/cv-api:latest \
  --memory 2 --cpu 1 \
  --registry-username <username> \
  --registry-password <password> \
  --ports 8000
```

---

## Part 4: Environment Configuration

### Development (`.env.dev`)
```bash
PYTHONUNBUFFERED=1
LOG_LEVEL=DEBUG
DEBUG=True
API_WORKERS=1
EMBEDDING_BATCH_SIZE=32
Database_Connection=sqlite:///local.db
Cache_Type=memory
```

### Production (`.env.prod`)
```bash
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
DEBUG=False
API_WORKERS=4
EMBEDDING_BATCH_SIZE=64
DATABASE_URL=postgresql://user:pass@db-host:5432/cvdb
CACHE_TYPE=redis
REDIS_URL=redis://cache-host:6379
SSL_CERT_DIR=/etc/ssl/certs
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cv-intelligence-config
data:
  LOG_LEVEL: "INFO"
  EMBEDDING_BATCH_SIZE: "64"
  FAISS_INDEX_TYPE: "IndexIVFFlat"
  API_WORKERS: "4"
---
apiVersion: v1
kind: Secret
metadata:
  name: cv-intelligence-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:pass@postgres-service:5432/cvdb
  REDIS_PASSWORD: your-redis-password
```

---

## Part 5: Scaling & Performance

### Horizontal Scaling

**Auto-scaling Configuration (AWS)**:

```bash
# Enable auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/cv-cluster/cv-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --policy-name cv-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/cv-cluster/cv-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'
```

### Load Balancing

**Nginx Configuration** (`nginx.conf`):

```nginx
upstream api_backend {
    server api:8000;
    server api:8000;  # Multiple instances
}

upstream dashboard_backend {
    server dashboard:8501;
}

server {
    listen 80;
    server_name cv.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cv.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # API routes
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Dashboard
    location / {
        proxy_pass http://dashboard_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
    }
}
```

### Caching Strategy

```python
# Redis caching for search results
from functools import lru_cache
import redis

cache = redis.Redis(host='cache-host', port=6379)

@app.get("/api/search")
@cache_with_ttl(ttl=3600)  # Cache 1 hour
def search(query: str, category: str = None):
    cache_key = f"search:{query}:{category}"
    
    # Check cache
    result = cache.get(cache_key)
    if result:
        return json.loads(result)
    
    # Perform search
    result = perform_search(query, category)
    
    # Cache result
    cache.setex(cache_key, 3600, json.dumps(result))
    
    return result
```

---

## Part 6: Monitoring & Logging

### Logging Setup

**Python Logging**:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # Console
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)
```

### CloudWatch Monitoring (AWS)

```bash
# View logs
aws logs tail /ecs/cv-intelligence --follow

# Create metric alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cv-api-high-cpu \
  --alarm-description "Alert if API CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
search_requests = Counter('cv_search_requests_total', 'Total search requests')
search_duration = Histogram('cv_search_duration_seconds', 'Search duration')
active_connections = Gauge('cv_active_connections', 'Active connections')

@app.get("/api/search")
def search(query: str):
    search_requests.inc()
    
    start_time = time.time()
    result = perform_search(query)
    duration = time.time() - start_time
    
    search_duration.observe(duration)
    return result

# Expose metrics
@app.get("/metrics")
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
```

---

## Part 7: Backup & Disaster Recovery

### Database Backups

```bash
# Automated PostgreSQL backup (daily at 2 AM)
# Add to crontab: 0 2 * * * /path/to/backup.sh

#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="cvdb"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U postgres $DB_NAME | gzip > $BACKUP_DIR/cvdb_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/cvdb_$DATE.sql.gz s3://your-backup-bucket/postgres/
```

### Data Snapshots

```bash
# EBS Snapshot (AWS)
aws ec2 create-snapshot --volume-id vol-xxx --description "CV data backup"

# Automated snapshots
aws ec2 create-snapshot-schedule \
  --volume-ids vol-xxx \
  --interval 24 \
  --retention 30
```

### Disaster Recovery Plan

**Recovery Time Objective (RTO)**: 1 hour  
**Recovery Point Objective (RPO)**: 1 hour

1. **Database Recovery**
   ```bash
   # Restore from backup
   gunzip < backup.sql.gz | psql -U postgres cvdb
   ```

2. **Model Cache Recovery**
   ```bash
   # Restore from S3
   aws s3 sync s3://backup-bucket/models/ /models/
   ```

3. **Service Restart**
   ```bash
   # Docker restart
   docker-compose restart
   
   # Kubernetes restart
   kubectl rollout restart deployment/cv-intelligence
   ```

---

## Part 8: Security Hardening

### SSL/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt with Certbot
certbot certonly --standalone -d cv.example.com
```

### API Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthCredential

security = HTTPBearer()

@app.get("/api/search")
def search(query: str, credentials: HTTPAuthCredential = Depends(security)):
    token = credentials.credentials
    
    # Validate token
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return perform_search(query)
```

### Environment Variables Security

```bash
# Use .env files (never commit to git)
echo ".env" >> .gitignore

# Run with environment file
docker run --env-file .env cv-api:latest

# Or use secrets manager
aws secretsmanager get-secret-value --secret-id cv/api-key
```

---

## Checklist: Production Deployment

- [ ] Docker images created and tested locally
- [ ] Environment variables configured (.env.prod)
- [ ] SSL/TLS certificates installed
- [ ] Database backups configured
- [ ] Monitoring and logging set up
- [ ] Auto-scaling configured
- [ ] Load balancer health checks enabled
- [ ] Security groups/network policies configured
- [ ] API documentation updated
- [ ] Runbooks/playbooks created
- [ ] Team trained on deployment process
- [ ] Disaster recovery plan tested
- [ ] Performance benchmarks validated
- [ ] Cost estimation completed

---

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs <service>`
2. Verify network connectivity: `curl http://localhost:8000/health`
3. Check environment variables: `docker exec <container> env`
4. Review Docker build output for errors

---

**Document Version**: 1.0  
**Last Updated**: March 20, 2026  
**Status**: Ready for Production
