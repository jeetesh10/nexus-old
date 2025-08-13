# Admin Dashboard Integration Protocol

## Overview

This document defines the protocol for automatically adding new services to the Nexus Admin Dashboard.

## Service Discovery Protocol

### 1. Kubernetes Label-Based Discovery

All services must include specific labels for automatic discovery:

```yaml
metadata:
  labels:
    app: <service-name>
    nexus.service.type: <service-category>  # Required
    nexus.service.description: <description> # Optional
    nexus.service.icon: <icon-emoji>        # Optional
    nexus.service.url: <service-url>        # Optional
    nexus.service.port: <port-number>       # Optional
```

### 2. Service Categories

Predefined service categories for automatic grouping:

- `database` - Database services (MongoDB, PostgreSQL)
- `auth` - Authentication services (Keycloak, Auth API)
- `monitoring` - Observability services (Prometheus, Grafana, Loki)
- `gateway` - API Gateway services (APISIX)
- `mesh` - Service Mesh services (Linkerd)
- `core` - Core platform services
- `custom` - Custom application services

### 3. Required Labels Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb-orchestrator
  labels:
    app: mongodb-orchestrator
    nexus.service.type: database
    nexus.service.description: "MongoDB Orchestrator Service"
    nexus.service.icon: "🗄️"
    nexus.service.url: "http://mongodb-orchestrator.local"
    nexus.service.port: "8000"
```

## Admin Dashboard Integration

### 1. Automatic Service Detection

The admin dashboard automatically discovers services using:

```python
# Service discovery logic
def discover_services():
    services = []
    deployments = k8s_client.list_deployment_for_all_namespaces()
    
    for deployment in deployments.items:
        if 'nexus.service.type' in deployment.metadata.labels:
            service = {
                'name': deployment.metadata.name,
                'type': deployment.metadata.labels['nexus.service.type'],
                'description': deployment.metadata.labels.get('nexus.service.description', ''),
                'icon': deployment.metadata.labels.get('nexus.service.icon', '🔧'),
                'url': deployment.metadata.labels.get('nexus.service.url', ''),
                'port': deployment.metadata.labels.get('nexus.service.port', '80'),
                'namespace': deployment.metadata.namespace,
                'replicas': deployment.spec.replicas,
                'status': get_pod_status(deployment.metadata.name, deployment.metadata.namespace)
            }
            services.append(service)
    
    return services
```

### 2. Service Grouping

Services are automatically grouped by category:

```python
def group_services_by_type(services):
    grouped = {}
    for service in services:
        service_type = service['type']
        if service_type not in grouped:
            grouped[service_type] = []
        grouped[service_type].append(service)
    return grouped
```

### 3. Dynamic UI Generation

The admin dashboard generates UI components based on service type:

```javascript
function generateServiceCard(service) {
    return `
        <div class="service-card" data-service-type="${service.type}">
            <div class="service-header">
                <span class="service-icon">${service.icon}</span>
                <h3>${service.name}</h3>
            </div>
            <div class="service-details">
                <p>${service.description}</p>
                <div class="service-status ${service.status}">${service.status}</div>
                <div class="service-replicas">${service.replicas} replicas</div>
            </div>
            <div class="service-actions">
                <button onclick="openService('${service.url}')">Open</button>
                <button onclick="restartService('${service.name}')">Restart</button>
            </div>
        </div>
    `;
}
```

## Implementation Steps

### Step 1: Update Existing Services

Add required labels to all existing services:

```bash
# Example: Update MongoDB Orchestrator
kubectl label deployment mongodb-orchestrator \
    nexus.service.type=database \
    nexus.service.description="MongoDB Orchestrator Service" \
    nexus.service.icon="🗄️" \
    nexus.service.url="http://mongodb-orchestrator.local" \
    nexus.service.port="8000" \
    -n default
```

### Step 2: Update Admin Dashboard

Modify the admin dashboard to use automatic discovery:

```python
# In admin-dashboard-service/src/main.py
def load_services():
    """Automatically discover and load services"""
    services = discover_services()
    grouped_services = group_services_by_type(services)
    return grouped_services
```

### Step 3: Service Template

Create a service template for new services:

```yaml
# templates/service-template.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <service-name>
  labels:
    app: <service-name>
    nexus.service.type: <category>
    nexus.service.description: "<description>"
    nexus.service.icon: "<icon>"
    nexus.service.url: "<url>"
    nexus.service.port: "<port>"
spec:
  # ... deployment spec
```

## Service Categories and Icons

| Category | Icon | Description |
|----------|------|-------------|
| `database` | 🗄️ | Database services |
| `auth` | 🔐 | Authentication services |
| `monitoring` | 📊 | Observability services |
| `gateway` | 🌐 | API Gateway services |
| `mesh` | 🕸️ | Service Mesh services |
| `core` | ⚙️ | Core platform services |
| `custom` | 🔧 | Custom application services |

## Benefits

1. **Automatic Discovery** - No manual configuration needed
2. **Consistent UI** - All services follow the same pattern
3. **Easy Maintenance** - Add/remove services by updating labels
4. **Scalable** - Works with any number of services
5. **Future-Proof** - Easy to extend with new categories

## Testing

Test the integration by:

1. Adding labels to a service
2. Refreshing the admin dashboard
3. Verifying the service appears in the correct category
4. Testing service actions (open, restart, etc.)
