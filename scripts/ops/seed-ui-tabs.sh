#!/usr/bin/env bash
set -euo pipefail

# Seed Mongo collection for data-driven Admin UI tabs
# Usage: ./scripts/ops/seed-ui-tabs.sh

MONGO_URI=${MONGODB_UI_URI:-"mongodb://mongodb-service.default.svc.cluster.local:27017"}
DB_NAME=${MONGODB_UI_DB:-"nexus"}
COLL=${MONGODB_UI_COLLECTION:-"ui_tabs"}

echo "Seeding UI tabs into ${MONGO_URI}/${DB_NAME}.${COLL}..."

mongosh "${MONGO_URI}/${DB_NAME}" --eval '
db.getCollection("ui_tabs").deleteMany({});
db.getCollection("ui_tabs").insertMany([
  { id: "services", name: "Services", icon: "📊", description: "Manage platform services", enabled: true, type: "internal", order: 1, required_groups: ["platform-admins"], show_on_landing: true },
  { id: "grafana", name: "Grafana", icon: "📈", description: "Monitoring dashboards", enabled: true, type: "external", url: "http://kube-prometheus-stack-grafana.monitoring:80", order: 2, required_groups: ["platform-admins", "monitoring-admin"], show_on_landing: true },
  { id: "prometheus", name: "Prometheus", icon: "📊", description: "Metrics explorer", enabled: true, type: "external", url: "http://kube-prometheus-stack-prometheus.monitoring:9090", order: 3, required_groups: ["platform-admins", "monitoring-admin"], show_on_landing: true },
  { id: "databases", name: "Databases", icon: "💾", description: "Mongo Express & Orchestrators", enabled: true, type: "internal", order: 4, required_groups: ["platform-admins", "service-admin"], show_on_landing: true }
]);
print("Seeded ui_tabs:");
printjson(db.getCollection("ui_tabs").find().toArray());
'

echo "Done."
