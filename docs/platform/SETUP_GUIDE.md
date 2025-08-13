# Nexus Project - Production-Ready Kubernetes Platform

## Overview

The Nexus Project is a foundational container infrastructure platform leveraging Docker and Kubernetes to establish a standardized, secure, and scalable environment for future containerized applications. This platform accelerates time-to-market for new services by providing pre-built infrastructure that handles core concerns like consistency, efficient deployment, and secure communication.

## Architecture

The platform consists of:

- **Kubernetes Cluster**: Local development using kind with persistent storage
- **Observability Stack**: Prometheus, Grafana, Alertmanager, and Loki for monitoring and logging
- **Admin Dashboard**: FastAPI-based service for managing and controlling other services
- **NGINX Ingress Controller**: Production-grade ingress for service routing
- **RBAC**: Fine-grained access control for security

## Prerequisites

- Docker Desktop (with at least 8GB RAM and 4 CPU cores allocated)
- kind v0.29.0+
- kubectl v1.33+
- Helm v3.18+

## Quick Start

### 1. Clone and Setup

```bash
cd Nexus
```

### 2. Create the Kubernetes Cluster

```bash
kind create cluster --config kind-config-persistent.yaml
```

### 3. Deploy the Observability Stack

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Deploy Prometheus stack
helm install nexus-observability prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace --values values-observability.yaml

# Deploy Loki for logging
helm install nexus-loki grafana/loki-stack --namespace monitoring --create-namespace --values values-observability.yaml

# Deploy Grafana separately (if needed)
helm install grafana grafana/grafana --namespace monitoring --set adminPassword=admin --set service.type=NodePort
```

### 4. Deploy NGINX Ingress Controller

```bash
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

### 5. Setup RBAC

```bash
kubectl apply -f admin-rbac.yaml
```

### 6. Build and Deploy Admin Dashboard

```bash
# Build the Docker image
cd admin-dashboard-service
docker build -t admin-dashboard-service:latest .

# Load image into kind cluster
kind load docker-image admin-dashboard-service:latest

# Deploy to Kubernetes
kubectl apply -f kubernetes/
```

### 7. Add Host Entry

```bash
echo "127.0.0.1 admin-dashboard.local" | sudo tee -a /etc/hosts
```

## Accessing Services

### 🎯 Unified Dashboard (Recommended)

**One URL to access everything!** The admin dashboard now includes a beautiful web interface with tabs for all services.

```bash
# Start the unified dashboard
./start-dashboard.sh
```

Then simply visit: **http://localhost:8081**

This single URL gives you access to:
- 📊 **Services Management** - View, start, and stop all services
- 📈 **Grafana** - Monitoring dashboards and visualizations
- 📊 **Prometheus** - Metrics and alerting rules
- 📝 **Loki** - Centralized log querying
- 🚨 **Alertmanager** - Alert management
- 🔧 **API Documentation** - Interactive API testing

### Alternative Access Methods

#### Quick Access Script

Use the provided access script to start all services:
```bash
./access-services.sh
```

This will start port-forwards for all services and keep them running.

### Manual Access

#### Admin Dashboard API

```bash
# Port forward to access the API
kubectl port-forward service/admin-dashboard-internal 8081:80

# Test the API
curl http://localhost:8081/api/services
curl -X POST http://localhost:8081/api/services/test-service/stop
curl -X POST http://localhost:8081/api/services/test-service/start
```

#### Grafana

```bash
# Port forward to access Grafana
kubectl port-forward service/grafana 3000:80 -n monitoring

# Access via browser
# http://localhost:3000
# Username: admin
# Password: admin
```

#### Loki (Logging)

```bash
# Port forward to access Loki
kubectl port-forward service/nexus-loki 3100:3100 -n monitoring

# Access via browser
# http://localhost:3100
```

#### Prometheus

```bash
# Port forward to access Prometheus
kubectl port-forward service/nexus-observability-kube-p-prometheus 9090:9090 -n monitoring

# Access via browser
# http://localhost:9090
```

#### Alertmanager

```bash
# Port forward to access Alertmanager
kubectl port-forward service/nexus-observability-kube-p-alertmanager 9093:9093 -n monitoring

# Access via browser
# http://localhost:9093
```

## API Endpoints

### Admin Dashboard API

- `GET /` - **Unified Dashboard** - Beautiful web interface with tabs for all services
- `GET /api/services` - List all services in the cluster
- `POST /api/services/{name}/stop` - Stop a service (scale to 0 replicas)
- `POST /api/services/{name}/start` - Start a service (scale to 1 replica)
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## Testing

### Test Service Management

1. Deploy a test service:
```bash
kubectl apply -f test-service.yaml
```

2. Verify it appears in the admin dashboard:
```bash
curl http://localhost:8081/api/services
```

3. Test stop/start functionality:
```bash
curl -X POST http://localhost:8081/api/services/test-service/stop
kubectl get pods -l app=test-service  # Should show no pods

curl -X POST http://localhost:8081/api/services/test-service/start
kubectl get pods -l app=test-service  # Should show running pod
```

## Monitoring and Observability

### Metrics Collection
- Prometheus scrapes metrics from all services
- Node exporter provides node-level metrics
- Kube-state-metrics provides Kubernetes object metrics

### Logging
- Loki collects logs from all pods via Promtail
- Logs can be queried in Grafana using LogQL

### Alerting
- Alertmanager handles alert routing and silencing
- Pre-configured alerts for common issues

## Security Features

- **RBAC**: Fine-grained permissions for the admin dashboard
- **Service Accounts**: Non-root containers with minimal privileges
- **Network Policies**: (Can be extended for additional security)
- **Secrets Management**: Kubernetes secrets for sensitive data

## Development Workflow

1. **Local Development**: Use the kind cluster for local testing
2. **Service Deployment**: Deploy services using standard Kubernetes manifests
3. **Monitoring**: All services are automatically monitored
4. **Management**: Use the admin dashboard to control services

## Troubleshooting

### Common Issues

1. **Pod not starting**: Check resource limits and image availability
2. **Ingress not working**: Verify ingress controller is running and service has endpoints
3. **Admin dashboard API errors**: Check RBAC permissions and service account

### Useful Commands

```bash
# Check cluster status
kubectl get nodes
kubectl get pods --all-namespaces

# Check service endpoints
kubectl get endpoints

# Check ingress status
kubectl get ingress

# View logs
kubectl logs -f deployment/admin-dashboard

# Check RBAC
kubectl describe clusterrole admin-dashboard-role
```

## Next Steps

1. **Add more services**: Deploy additional microservices
2. **Implement CI/CD**: Set up automated deployment pipelines
3. **Add security policies**: Implement network policies and pod security standards
4. **Scale the platform**: Add more nodes and implement horizontal scaling
5. **Production deployment**: Deploy to cloud Kubernetes services (EKS, GKE, AKS)

## Contributing

Follow the coding best practices defined in `.cursor/rules`:
- No hardcoded values
- No environment-specific naming
- Comprehensive testing
- Proper error handling
- Security-first approach

## License

This project follows the development guidelines and best practices outlined in the project documentation.
