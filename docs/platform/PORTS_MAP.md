Nexus local port map

- Admin Dashboard + Landing: localhost:8081 (override with DASHBOARD_LOCAL_PORT)
- Keycloak (port-forwarded): localhost:9080
- Grafana: localhost:3000
- Prometheus: localhost:9090
- Alertmanager: localhost:9093
- Loki: localhost:3100
- Mongo Express (local docker-compose): localhost:8082 → container 8081

Notes
- In-cluster, the admin dashboard Service is admin-dashboard-internal:80 → Pod 8000.
- The start script forwards admin-dashboard-internal:80 to your local 8081 by default.
- If 8081 is already used, the script falls back to 18081 or you can set DASHBOARD_LOCAL_PORT.
- Mongo Express in Kubernetes uses Service port 8081, but you should not forward it on 8081 locally; access it via the dashboard proxy at /proxy/mongo-express/ or run the local docker version on 8082.