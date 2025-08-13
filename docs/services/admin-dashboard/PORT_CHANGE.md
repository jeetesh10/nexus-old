# Port Configuration Update

## Summary
Changed the Nexus Admin Dashboard port from **8080** to **8081** to avoid conflicts with Keycloak.

## Why This Change?
- Keycloak by default uses port 8080
- To avoid port conflicts when deploying Keycloak later
- Ensures smooth integration of authentication services

## Updated Ports

| Service | Old Port | New Port | Purpose |
|---------|----------|----------|---------|
| Admin Dashboard | 8080 | **8081** | Unified management interface |
| Grafana | 3000 | 3000 | Monitoring dashboards |
| Prometheus | 9090 | 9090 | Metrics and alerting |
| Loki | 3100 | 3100 | Log aggregation |
| Alertmanager | 9093 | 9093 | Alert management |

## Updated URLs

### Primary Access
- **Unified Dashboard**: http://localhost:8081
- **API Endpoint**: http://localhost:8081/api/services

### Individual Services
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Alertmanager**: http://localhost:9093

## Updated Scripts
- `start-dashboard.sh` - Now uses port 8081
- `access-services.sh` - Now uses port 8081
- `verify-setup.sh` - Updated test URLs

## Commands Updated
```bash
# Old command
kubectl port-forward service/admin-dashboard-internal 8080:80

# New command
kubectl port-forward service/admin-dashboard-internal 8081:80
```

## Next Steps
When deploying Keycloak:
- Keycloak can use port 8080 (default)
- Admin Dashboard will use port 8081
- No port conflicts expected

## Testing
To verify the change:
```bash
# Start the dashboard
./start-dashboard.sh

# Test the new port
curl http://localhost:8081/api/services
```
