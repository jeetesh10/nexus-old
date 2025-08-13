#!/bin/bash

echo "🔧 Setting Up Real Data for Nexus Observability Stack"
echo "====================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

# 1. Configure Prometheus Alert Rules
echo -e "${BLUE}📊 Configuring Prometheus Alert Rules...${NC}"

kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: nexus-alerts
  namespace: monitoring
  labels:
    release: nexus-observability
spec:
  groups:
  - name: nexus.alerts
    rules:
    # High CPU Usage Alert
    - alert: HighCPUUsage
      expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 70
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage on {{ \$labels.instance }}"
        description: "CPU usage is above 70% for more than 2 minutes on {{ \$labels.instance }}"
    
    # High Memory Usage Alert
    - alert: HighMemoryUsage
      expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 80
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage on {{ \$labels.instance }}"
        description: "Memory usage is above 80% for more than 2 minutes on {{ \$labels.instance }}"
    
    # Pod Restart Alert
    - alert: PodRestarting
      expr: increase(kube_pod_container_status_restarts_total[10m]) > 0
      for: 1m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ \$labels.pod }} is restarting"
        description: "Pod {{ \$labels.pod }} in namespace {{ \$labels.namespace }} has restarted {{ \$value }} times in the last 10 minutes"
    
    # Service Down Alert
    - alert: ServiceDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Service {{ \$labels.job }} is down"
        description: "Service {{ \$labels.job }} has been down for more than 1 minute"
    
    # Admin Dashboard High Response Time
    - alert: AdminDashboardHighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="admin-dashboard"}[5m])) > 1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Admin Dashboard high response time"
        description: "95th percentile response time is above 1 second"
    
    # Disk Space Alert
    - alert: DiskSpaceFilling
      expr: (node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"} < 30
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Disk space filling up on {{ \$labels.instance }}"
        description: "Disk space is below 30% on {{ \$labels.instance }}"
EOF

# 2. Create services that generate real logs and metrics
echo -e "${BLUE}📝 Creating services that generate real data...${NC}"

# Create a web application that generates logs and metrics
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-webapp
  labels:
    app: sample-webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-webapp
  template:
    metadata:
      labels:
        app: sample-webapp
    spec:
      containers:
      - name: webapp
        image: nginx:alpine
        ports:
        - containerPort: 80
        env:
        - name: NGINX_ACCESS_LOG
          value: "/var/log/nginx/access.log"
        - name: NGINX_ERROR_LOG
          value: "/var/log/nginx/error.log"
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    events {
        worker_connections 1024;
    }
    http {
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
        
        server {
            listen 80;
            location / {
                return 200 "Hello from Sample WebApp!";
                add_header Content-Type text/plain;
            }
            location /health {
                return 200 "healthy";
                add_header Content-Type text/plain;
            }
            location /metrics {
                return 200 "http_requests_total{method=\"GET\",status=\"200\"} 1";
                add_header Content-Type text/plain;
            }
        }
    }
---
apiVersion: v1
kind: Service
metadata:
  name: sample-webapp
  labels:
    app: sample-webapp
spec:
  selector:
    app: sample-webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
EOF

# Create a log generator that produces structured logs
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
            echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Application started successfully"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Processing request from user 12345"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] High memory usage detected: 85%"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Database connection failed: timeout"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Request completed in 150ms"
            echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Cache hit ratio: 92%"
            sleep 3
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

# 3. Create a load generator to generate metrics
echo -e "${BLUE}📈 Creating load generator for metrics...${NC}"

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  labels:
    app: load-generator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: load-generator
  template:
    metadata:
      labels:
        app: load-generator
    spec:
      containers:
      - name: load-generator
        image: busybox
        command: ["/bin/sh"]
        args:
        - -c
        - |
          while true; do
            # Generate load on admin dashboard
            curl -s http://admin-dashboard-internal/api/services > /dev/null 2>&1 || true
            curl -s http://admin-dashboard-internal/health > /dev/null 2>&1 || true
            
            # Generate load on sample webapp
            curl -s http://sample-webapp/ > /dev/null 2>&1 || true
            curl -s http://sample-webapp/health > /dev/null 2>&1 || true
            
            # Random delays to simulate real traffic
            sleep $((RANDOM % 5 + 1))
          done
        resources:
          requests:
            cpu: "10m"
            memory: "32Mi"
          limits:
            cpu: "100m"
            memory: "64Mi"
EOF

# 4. Configure Grafana with real dashboards
echo -e "${BLUE}📊 Configuring Grafana dashboards...${NC}"

# Get Grafana admin password
GRAFANA_PASSWORD=$(kubectl get secret grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d 2>/dev/null || echo "admin")

# Wait for Grafana to be ready
sleep 10

# Create a comprehensive dashboard
curl -X POST http://admin:${GRAFANA_PASSWORD}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Nexus Platform Overview",
      "tags": ["nexus", "platform"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Cluster CPU Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "legendFormat": "{{instance}}"
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
                  {"color": "yellow", "value": 70},
                  {"color": "red", "value": 90}
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
              "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
              "legendFormat": "{{instance}}"
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
                  {"color": "yellow", "value": 80},
                  {"color": "red", "value": 90}
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
        },
        {
          "id": 4,
          "title": "HTTP Request Rate",
          "type": "graph",
          "targets": [
            {
              "expr": "rate(http_requests_total[5m])",
              "legendFormat": "{{job}}"
            }
          ],
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
        },
        {
          "id": 5,
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
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
        }
      ],
      "time": {"from": "now-15m", "to": "now"},
      "refresh": "5s"
    }
  }' 2>/dev/null || echo "Dashboard already exists"

# 5. Configure Alertmanager
echo -e "${BLUE}🚨 Configuring Alertmanager...${NC}"

kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
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
kubectl rollout restart statefulset/alertmanager-nexus-observability-kube-p-alertmanager -n monitoring

# 6. Generate some test alerts
echo -e "${BLUE}⚠️ Generating test alerts...${NC}"

# Create a service that will trigger alerts
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alert-trigger
  labels:
    app: alert-trigger
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alert-trigger
  template:
    metadata:
      labels:
        app: alert-trigger
    spec:
      containers:
      - name: alert-trigger
        image: busybox
        command: ["/bin/sh"]
        args:
        - -c
        - |
          while true; do
            # Simulate high CPU usage
            for i in {1..100}; do
              echo "Generating load to trigger alerts..."
              sleep 0.1
            done
            sleep 30
          done
        resources:
          requests:
            cpu: "200m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
EOF

# 7. Wait for everything to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 15

# 8. Test the setup
echo -e "${GREEN}✅ Real data setup complete!${NC}"
echo -e "\n${YELLOW}What you should now see:${NC}"

echo -e "\n${BLUE}📊 Prometheus (http://localhost:9090):${NC}"
echo -e "  - Go to 'Graph' tab"
echo -e "  - Try these queries:"
echo -e "    * up (shows all services)"
echo -e "    * active_services (shows running services count)"
echo -e "    * rate(http_requests_total[5m]) (shows request rate)"
echo -e "    * node_cpu_seconds_total (shows CPU usage)"

echo -e "\n${BLUE}📝 Loki (http://localhost:3100):${NC}"
echo -e "  - Go to 'Query' tab"
echo -e "  - Try these queries:"
echo -e "    * {app=\"log-generator\"} (shows log generator logs)"
echo -e "    * {app=\"sample-webapp\"} (shows webapp logs)"
echo -e "    * {level=\"ERROR\"} (shows error logs)"

echo -e "\n${BLUE}🚨 Alertmanager (http://localhost:9093):${NC}"
echo -e "  - Should show active alerts"
echo -e "  - Check 'Alerts' tab for triggered alerts"

echo -e "\n${BLUE}📈 Grafana (http://localhost:3000):${NC}"
echo -e "  - Login with admin/${GRAFANA_PASSWORD}"
echo -e "  - Check 'Nexus Platform Overview' dashboard"
echo -e "  - Should show real metrics and charts"

echo -e "\n${BLUE}📊 Admin Dashboard (http://localhost:8081):${NC}"
echo -e "  - Should show animated charts with real data"
echo -e "  - Try 'Load Embedded Dashboard' buttons"

echo -e "\n${YELLOW}If you don't see data immediately, wait a few minutes for metrics to accumulate.${NC}"
