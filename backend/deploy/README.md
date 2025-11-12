# Project AEGIS Deployment Guide

## Overview

Project AEGIS (Advanced Cybercrime Response System) is a comprehensive cybercrime response platform with AI-powered prediction capabilities, real-time monitoring, and multi-channel alert systems.

## Architecture

The system consists of multiple microservices deployed on Kubernetes:

- **Backend API**: FastAPI-based REST API with WebSocket support
- **Database**: PostgreSQL with PostGIS for geospatial capabilities
- **Cache**: Redis for caching and session management
- **Messaging**: Apache Kafka for real-time data streaming
- **Monitoring**: Prometheus, Grafana, and Jaeger for observability
- **Logging**: Elasticsearch and Kibana for log aggregation

## Prerequisites

### Kubernetes Cluster Requirements

- **Kubernetes Version**: 1.24+
- **Nodes**: Minimum 3 nodes (1 control plane, 2 workers)
- **Node Requirements**:
  - **Control Plane**: 4 vCPU, 8GB RAM, 100GB SSD
  - **Worker Nodes**: 8 vCPU, 16GB RAM, 200GB SSD
- **Storage**: Dynamic provisioning with appropriate storage classes
- **Networking**: LoadBalancer support or Ingress controller

### External Dependencies

- **PostgreSQL**: Version 15+ with PostGIS extension
- **Redis**: Version 7+
- **Apache Kafka**: Version 3.4+
- **NPCI APIs**: For digital payment interception
- **NCRP APIs**: For cybercrime reporting integration
- **I4C APIs**: For historical crime data
- **CFCFRMS APIs**: For financial crime monitoring

### Required Tools

- `kubectl` configured for your cluster
- `helm` 3.0+ (if using Helm charts)
- `docker` for building images
- Cloud provider CLI tools (aws-cli, gcloud, etc.)

## Deployment Steps

### 1. Prepare the Environment

#### Clone the Repository
```bash
git clone https://github.com/aegis-project/backend.git
cd aegis/backend/deploy
```

#### Create Namespace
```bash
kubectl apply -f kubernetes/namespace.yaml
```

#### Create Secrets
⚠️ **Important**: Update the secrets with your actual values before applying.

```bash
# Update secrets.yaml with actual values
vim kubernetes/secrets.yaml

# Apply secrets
kubectl apply -f kubernetes/secrets.yaml
```

### 2. Deploy Infrastructure

#### Deploy Persistent Volumes
```bash
kubectl apply -f kubernetes/persistent-volumes.yaml
```

#### Deploy Database (PostgreSQL)
```bash
# Deploy PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --namespace aegis \
  --set auth.postgresPassword=$(kubectl get secret aegis-secrets -n aegis -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d) \
  --set auth.database=aegis_db \
  --set auth.username=aegis_user \
  --set primary.persistence.existingClaim=postgres-data-pvc \
  --set primary.service.type=ClusterIP \
  --set primary.extraEnvVars[0].name=POSTGRES_INITDB_ARGS
  --set primary.extraEnvVars[0].value="--encoding=UTF8 --locale=C"

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n aegis --timeout=300s
```

#### Deploy Redis
```bash
helm install redis bitnami/redis \
  --namespace aegis \
  --set auth.password=$(kubectl get secret aegis-secrets -n aegis -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d) \
  --set master.persistence.existingClaim=redis-data-pvc \
  --set replica.replicaCount=2 \
  --set master.service.type=ClusterIP

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n aegis --timeout=300s
```

#### Deploy Kafka
```bash
helm install kafka bitnami/kafka \
  --namespace aegis \
  --set persistence.existingClaim=kafka-data-pvc \
  --set zookeeper.persistence.existingClaim=kafka-data-pvc \
  --set replicaCount=3 \
  --set offsetLogsTopic.replicationFactor=3 \
  --set transactionStateLogReplicationFactor=3 \
  --set defaultReplicationFactor=3 \
  --set service.type=ClusterIP

# Wait for Kafka to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka -n aegis --timeout=300s
```

### 3. Deploy Application

#### Deploy ConfigMaps
```bash
kubectl apply -f kubernetes/configmap.yaml
```

#### Deploy Backend Application
```bash
kubectl apply -f kubernetes/deployment.yaml
```

#### Deploy Services
```bash
kubectl apply -f kubernetes/service.yaml
```

### 4. Deploy Monitoring Stack

#### Deploy Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace aegis \
  --create-namespace \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.accessModes=["ReadWriteOnce"] \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=aegis-fast-storage \
  --set grafana.adminPassword=$(kubectl get secret aegis-secrets -n aegis -o jsonpath='{.data.GRAFANA_PASSWORD}' | base64 -d) \
  --set grafana.persistence.existingClaim=grafana-data-pvc
```

#### Deploy Jaeger
```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace aegis \
  --set provisionDataStore.cassandra=false \
  --set provisionDataStore.elasticsearch=false \
  --set storage.type=memory \
  --set memory.maxTraces=50000 \
  --set persistence.existingClaim=jaeger-data-pvc
```

#### Deploy Elasticsearch and Kibana
```bash
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch \
  --namespace aegis \
  --set replicas=3 \
  --set volumeClaimTemplate.resources.requests.storage=200Gi \
  --set minimumMasterNodes=2

helm install kibana elastic/kibana \
  --namespace aegis \
  --set service.type=LoadBalancer \
  --set service.port=5601
```

### 5. Configure External Services

#### Update DNS Records
```bash
# Get the LoadBalancer IP
kubectl get svc aegis-backend-service -n aegis

# Update DNS records for:
# - aegis.gov.in → LoadBalancer IP
# - api.aegis.gov.in → LoadBalancer IP
# - admin.aegis.gov.in → LoadBalancer IP
```

#### Configure SSL Certificates
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@aegis.gov.in
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 6. Initialize Database

#### Run Database Migrations
```bash
# Get a pod to run migrations in
POD_NAME=$(kubectl get pods -n aegis -l app=aegis,component=backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -n aegis $POD_NAME -- python -m alembic upgrade head
```

#### Seed Initial Data
```bash
kubectl exec -n aegis $POD_NAME -- python scripts/seed_data.py
```

### 7. Verify Deployment

#### Check Pod Status
```bash
kubectl get pods -n aegis
kubectl get services -n aegis
kubectl get ingress -n aegis
```

#### Test Health Endpoints
```bash
# Get LoadBalancer IP
LB_IP=$(kubectl get svc aegis-backend-service -n aegis -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://$LB_IP/health

# Test API endpoint
curl http://$LB_IP/api/v1/system/status
```

#### Check Logs
```bash
# Check backend logs
kubectl logs -n aegis -l app=aegis,component=backend -f

# Check database logs
kubectl logs -n aegis -l app.kubernetes.io/name=postgres -f
```

## Configuration

### Environment Variables

Key environment variables that can be customized:

- **AEGIS_ENV**: Environment (development/staging/production)
- **LOG_LEVEL**: Logging level (DEBUG/INFO/WARNING/ERROR)
- **WORKERS**: Number of worker processes
- **RATE_LIMIT_PER_MINUTE**: Rate limiting threshold
- **ENABLE_METRICS**: Enable/disable metrics collection

### Scaling

#### Horizontal Scaling
```bash
# Scale backend replicas
kubectl scale deployment aegis-backend --replicas=10 -n aegis

# Update HPA limits
kubectl patch hpa aegis-backend-hpa -n aegis -p '{"spec":{"maxReplicas":50}}'
```

#### Vertical Scaling
```bash
# Update resource limits
kubectl patch deployment aegis-backend -n aegis -p '{"spec":{"template":{"spec":{"containers":[{"name":"aegis-backend","resources":{"limits":{"memory":"4Gi","cpu":"2000m"}}}]}}}'
```

## Monitoring and Troubleshooting

### Health Checks

- **Application Health**: `/health` endpoint
- **Database Health**: Check PostgreSQL pod status
- **Cache Health**: Check Redis pod status
- **Message Queue Health**: Check Kafka pod status

### Monitoring Dashboards

Access monitoring dashboards at:

- **Grafana**: http://<LoadBalancer-IP>:3000 (admin/admin123)
- **Prometheus**: http://<LoadBalancer-IP>:9090
- **Jaeger**: http://<LoadBalancer-IP>:16686
- **Kibana**: http://<LoadBalancer-IP>:5601

### Common Issues

#### Pod Crashing
```bash
# Check pod logs
kubectl logs <pod-name> -n aegis

# Check pod events
kubectl describe pod <pod-name> -n aegis
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it <postgres-pod> -n aegis -- psql -U aegis_user -d aegis_db

# Check database service
kubectl get svc postgres-service -n aegis
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n aegis

# Check HPA status
kubectl get hpa -n aegis
```

## Backup and Recovery

### Database Backup
```bash
# Create backup
kubectl exec -n aegis postgres-0 -- pg_dump -U aegis_user aegis_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
kubectl exec -i -n aegis postgres-0 -- psql -U aegis_user aegis_db < backup_file.sql
```

### Application Backup
```bash
# Backup persistent volumes
kubectl get pvc -n aegis

# Use cloud provider backup solutions for volume backups
```

## Security

### Network Policies
- Network policies are configured to restrict traffic between services
- Only necessary ports are exposed
- External API communication is controlled

### Secrets Management
- All sensitive data is stored in Kubernetes secrets
- Secrets are encrypted at rest
- Regular key rotation is recommended

### RBAC
- Service accounts are created with minimal required permissions
- Role-based access control is implemented

## Performance Tuning

### Database Optimization
- Configure PostgreSQL work_mem and shared_buffers
- Monitor slow queries and add appropriate indexes
- Use connection pooling

### Application Optimization
- Adjust worker count based on available resources
- Enable caching for frequently accessed data
- Monitor and tune garbage collection

### Kubernetes Optimization
- Use node affinity for better resource utilization
- Configure pod anti-affinity for high availability
- Optimize resource requests and limits

## Maintenance

### Rolling Updates
```bash
# Update application image
kubectl set image deployment/aegis-backend aegis-backend=aegis/backend:2.0.1 -n aegis

# Monitor rollout status
kubectl rollout status deployment/aegis-backend -n aegis
```

### Scheduled Maintenance
```bash
# Scale down for maintenance
kubectl scale deployment aegis-backend --replicas=0 -n aegis

# Perform maintenance tasks
# ...

# Scale back up
kubectl scale deployment aegis-backend --replicas=3 -n aegis
```

## Support

For support and issues:

1. Check the troubleshooting section above
2. Review logs in Kibana: http://<LoadBalancer-IP>:5601
3. Check system health in Grafana: http://<LoadBalancer-IP>:3000
4. Contact the AEGIS support team at support@aegis.gov.in

## Version History

- **v2.0.0**: Current production version
- **v1.x.x**: Legacy versions (deprecated)

---

**Note**: This deployment guide assumes you have the necessary permissions and access to the required external services. Adjust configurations based on your specific environment and requirements.