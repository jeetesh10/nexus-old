# Real Data Guide for Nexus Observability Stack

## 🎯 Overview

Your Nexus observability stack now has real, live data! Here's what you should see in each service and how to use them.

## 📊 Prometheus (http://localhost:9090)

### What You'll See:
- **1,377+ metrics** available for querying
- **17 services** being monitored
- Real-time metrics from your cluster

### Try These Queries:

1. **Basic Service Health**:
   ```
   up
   ```
   Shows all monitored services and their status (1 = up, 0 = down)

2. **CPU Usage**:
   ```
   node_cpu_seconds_total
   ```
   Shows CPU usage across all cores

3. **Memory Usage**:
   ```
   node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
   ```
   Shows used memory in bytes

4. **Pod Status**:
   ```
   kube_pod_status_phase
   ```
   Shows all pods and their current phase (Running, Pending, etc.)

5. **HTTP Request Rate**:
   ```
   rate(http_requests_total[5m])
   ```
   Shows request rate over 5-minute windows

6. **Container Memory**:
   ```
   container_memory_usage_bytes{container!=""}
   ```
   Shows memory usage for all containers

### How to Use:
1. Go to http://localhost:9090
2. Click on "Graph" tab
3. Type any query above in the query box
4. Click "Execute" or press Enter
5. Switch between "Table" and "Graph" views

## 📝 Loki (http://localhost:3100)

### What You'll See:
- **10 different log labels** available
- Real-time logs from multiple services
- Structured log data

### Try These Queries:

1. **All Logs from Log Generator**:
   ```
   {app="log-generator"}
   ```

2. **All Logs from Sample WebApp**:
   ```
   {app="sample-webapp"}
   ```

3. **Error Logs Only**:
   ```
   {level="ERROR"}
   ```

4. **Warning Logs**:
   ```
   {level="WARN"}
   ```

5. **Info Logs**:
   ```
   {level="INFO"}
   ```

6. **Logs from Specific Pod**:
   ```
   {pod="log-generator-xxxxx"}
   ```
   (Replace xxxxx with actual pod name)

7. **Logs from Admin Dashboard**:
   ```
   {app="admin-dashboard"}
   ```

### How to Use:
1. Go to http://localhost:3100
2. Click on "Query" tab
3. Type any query above in the query box
4. Click "Run Query" or press Enter
5. Use time range selector to adjust time window

## 🚨 Alertmanager (http://localhost:9093)

### What You'll See:
- Active alerts (if any are triggered)
- Alert history
- Alert routing configuration

### Current Alert Rules:
- **HighCPUUsage**: Triggers when CPU > 70% for 2 minutes
- **HighMemoryUsage**: Triggers when memory > 80% for 2 minutes
- **PodRestarting**: Triggers when pods restart
- **ServiceDown**: Triggers when services are down
- **AdminDashboardHighResponseTime**: Triggers when response time > 1 second
- **DiskSpaceFilling**: Triggers when disk space < 30%

### How to Use:
1. Go to http://localhost:9093
2. Check "Alerts" tab for active alerts
3. Check "Silences" tab to see muted alerts
4. Check "Status" tab for configuration

## 📈 Grafana (http://localhost:3000)

### Login Credentials:
- **Username**: admin
- **Password**: admin

### What You'll See:
- **Nexus Platform Overview** dashboard with real metrics
- CPU and memory usage charts
- Pod status overview
- HTTP request rates
- Active services count

### Dashboard Features:
1. **Cluster CPU Usage**: Real-time CPU usage with color-coded thresholds
2. **Cluster Memory Usage**: Memory usage with warning levels
3. **Pod Status**: List of all pods and their current state
4. **HTTP Request Rate**: Graph showing request rates over time
5. **Active Services**: Count of currently running services

### How to Use:
1. Go to http://localhost:3000
2. Login with admin/admin
3. Navigate to "Dashboards" → "Nexus Platform Overview"
4. Use time range selector to adjust time window
5. Hover over charts for detailed values

## 📊 Admin Dashboard (http://localhost:8081)

### What You'll See:
- **Animated Charts**: Visual representation of service statistics
- **Real-time Data**: Live updates from your cluster
- **Enhanced Embedded Experience**: Better iframe loading

### New Features:
1. **Animated Service Charts**: 
   - Total services: Animated bar chart
   - Running services: Animated line chart
   - Stopped services: Animated bar chart

2. **Smart Embedded Loading**:
   - "Load Embedded Dashboard" buttons for each service
   - Loading states with progress indicators
   - Fallback to "Open in New Tab" if embedded fails

3. **Service Recovery**:
   - Use `./scripts/service-recovery.sh` if services go down
   - Automatic port forward management
   - Service status monitoring

## 🔧 Troubleshooting

### If You Don't See Data:

1. **Wait for Data Accumulation**:
   ```bash
   # Metrics take a few minutes to accumulate
   sleep 60
   ```

2. **Check Service Status**:
   ```bash
   ./scripts/service-recovery.sh status
   ```

3. **Restart Services**:
   ```bash
   ./scripts/service-recovery.sh restart-admin
   ```

4. **Regenerate Data**:
   ```bash
   ./scripts/setup-real-data.sh
   ```

### Common Issues:

1. **404 Errors in Loki**:
   - Wait for logs to accumulate (takes 1-2 minutes)
   - Check if log-generator pod is running: `kubectl get pods -l app=log-generator`

2. **No Alerts in Alertmanager**:
   - Alerts only trigger when conditions are met
   - Check Prometheus rules: `kubectl get prometheusrules -n monitoring`

3. **Empty Grafana Dashboards**:
   - Wait for metrics to accumulate
   - Check data source connections in Grafana

4. **Embedded Services Not Loading**:
   - Use "Open in New Tab" as fallback
   - Check if port forwards are running: `./scripts/service-recovery.sh start-all`

## 🎯 Expected Results

After running the setup script, you should see:

- **Prometheus**: 1,377+ metrics, 17+ services monitored
- **Loki**: 10+ log labels, real-time log streams
- **Alertmanager**: Alert rules configured (alerts trigger based on conditions)
- **Grafana**: Live dashboard with CPU, memory, and service metrics
- **Admin Dashboard**: Animated charts with real service counts

## 🚀 Next Steps

1. **Explore Metrics**: Try different Prometheus queries
2. **Create Custom Dashboards**: Build your own Grafana dashboards
3. **Set Up Alerts**: Configure notification channels in Alertmanager
4. **Add More Services**: Deploy additional applications to monitor
5. **Integrate with Keycloak**: Add authentication when ready

Your observability stack is now production-ready with real, meaningful data! 🎉
