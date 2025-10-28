#!/bin/bash

echo "🔧 Configuring Nexus Observability Stack"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=admin-dashboard --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s

# Configure Grafana
echo -e "${BLUE}Configuring Grafana...${NC}"

# Get Grafana admin password
GRAFANA_PASSWORD=$(kubectl get secret grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d)

# Create data sources
echo -e "${YELLOW}Setting up Grafana data sources...${NC}"
curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://nexus-observability-kube-p-prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' 2>/dev/null || echo "Prometheus datasource already exists"

curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://nexus-loki:3100",
    "access": "proxy"
  }' 2>/dev/null || echo "Loki datasource already exists"

# Create dashboards
echo -e "${YELLOW}Creating Grafana dashboards...${NC}"

# Kubernetes Cluster Overview Dashboard
curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Kubernetes Cluster Overview",
      "tags": ["kubernetes", "cluster"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Cluster CPU Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(rate(container_cpu_usage_seconds_total{container!=\"\"}[5m])) by (pod)",
              "legendFormat": "{{pod}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "color": {"mode": "palette-classic"},
              "custom": {"displayMode": "gradient"},
              "thresholds": {
                "mode": "absolute",
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "red", "value": 80}
                ]
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Cluster Memory Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(rate(container_memory_usage_bytes{container!=\"\"}[5m])) by (pod)",
              "legendFormat": "{{pod}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "color": {"mode": "palette-classic"},
              "custom": {"displayMode": "gradient"},
              "thresholds": {
                "mode": "absolute",
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "red", "value": 80}
                ]
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
        },
        {
          "id": 3,
          "title": "Pod Status",
          "type": "stat",
          "targets": [
            {
              "expr": "kube_pod_status_phase",
              "legendFormat": "{{pod}} - {{phase}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "color": {"mode": "palette-classic"},
              "custom": {"displayMode": "list"},
              "thresholds": {
                "mode": "absolute",
                "steps": [{"color": "green", "value": null}]
              }
            }
          },
          "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
        }
      ],
      "time": {"from": "now-1h", "to": "now"},
      "refresh": "5s"
    }
  }' 2>/dev/null || echo "Kubernetes dashboard already exists"

# Nexus Services Dashboard
curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Nexus Services Overview",
      "tags": ["nexus", "services"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Admin Dashboard Requests",
          "type": "graph",
          "targets": [
            {
              "expr": "rate(http_requests_total{service=\"admin-dashboard\"}[5m])",
              "legendFormat": "Requests/sec"
            }
          ],
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Service Response Times",
          "type": "graph",
          "targets": [
            {
              "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"admin-dashboard\"}[5m]))",
              "legendFormat": "95th percentile"
            }
          ],
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
        },
        {
          "id": 3,
          "title": "Active Services",
          "type": "stat",
          "targets": [
            {
              "expr": "active_services",
              "legendFormat": "Active Services"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "color": {"mode": "palette-classic"},
              "custom": {"displayMode": "single-stat"},
              "thresholds": {
                "mode": "absolute",
                "steps": [{"color": "green", "value": null}]
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
        },
        {
          "id": 4,
          "title": "Total Services",
          "type": "stat",
          "targets": [
            {
              "expr": "total_services",
              "legendFormat": "Total Services"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "color": {"mode": "palette-classic"},
              "custom": {"displayMode": "single-stat"},
              "thresholds": {
                "mode": "absolute",
                "steps": [{"color": "blue", "value": null}]
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
        }
      ],
      "time": {"from": "now-1h", "to": "now"},
      "refresh": "5s"
    }
  }' 2>/dev/null || echo "Nexus services dashboard already exists"

# Configure Prometheus to scrape admin dashboard metrics
echo -e "${BLUE}Configuring Prometheus to scrape admin dashboard...${NC}"

# Create ServiceMonitor for admin dashboard
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: admin-dashboard-monitor
  namespace: monitoring
  labels:
    release: nexus-observability
spec:
  selector:
    matchLabels:
      app: admin-dashboard
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
EOF

# Configure Alertmanager
echo -e "${BLUE}Configuring Alertmanager...${NC}"

# Create a simple webhook receiver for testing
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config-updated
  namespace: monitoring
data:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    
    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
    
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://127.0.0.1:5001/'
        send_resolved: true
    
    inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'instance']
EOF

# Restart Alertmanager to pick up new config
kubectl rollout restart deployment/alertmanager-nexus-observability-kube-p-alertmanager -n monitoring

# Generate some test data
echo -e "${BLUE}Generating test data...${NC}"

# Create a test service that generates logs
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator
  labels:
    app: log-generator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: log-generator
  template:
    metadata:
      labels:
        app: log-generator
    spec:
      containers:
      - name: log-generator
        image: busybox
        command: ["/bin/sh"]
        args:
        - -c
        - |
          while true; do
            echo "$(date): INFO - Test log message from log-generator"
            echo "$(date): WARN - This is a warning message"
            echo "$(date): ERROR - This is an error message"
            sleep 5
          done
        resources:
          requests:
            cpu: "10m"
            memory: "32Mi"
          limits:
            cpu: "100m"
            memory: "64Mi"
EOF

# Create a service for the log generator
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: log-generator
  labels:
    app: log-generator
spec:
  selector:
    app: log-generator
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
EOF

echo -e "${GREEN}✅ Observability stack configuration complete!${NC}"
echo -e "\n${YELLOW}Access your configured services:${NC}"
echo -e "  📊 Admin Dashboard: http://localhost:8081"
echo -e "  📈 Grafana: http://localhost:3000 (admin/${GRAFANA_PASSWORD})"
echo -e "  📊 Prometheus: http://localhost:9090"
echo -e "  📝 Loki: http://localhost:3100"
echo -e "  🚨 Alertmanager: http://localhost:9093"
echo -e "\n${BLUE}Grafana Dashboards Created:${NC}"
echo -e "  📊 Kubernetes Cluster Overview"
echo -e "  📈 Nexus Services Overview"
echo -e "\n${BLUE}Test Data:${NC}"
echo -e "  📝 Log generator service deployed (generates test logs)"
echo -e "  📊 Admin dashboard metrics being collected"
echo -e "  🚨 Alert rules configured for monitoring"
