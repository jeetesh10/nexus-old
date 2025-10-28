# UI Tabs Schema (Admin Dashboard)

The Admin Dashboard navigation and the public landing page are fully data-driven.
Tabs are stored in MongoDB and fetched via:

- GET /api/ui/tabs (admin-only; used by the dashboard sidebar)
- GET /api/ui/public (public; used by landing page tiles)

Configure the Admin deployment with these env vars:
- MONGODB_UI_URI: MongoDB connection string (e.g., mongodb://mongodb-service.default.svc.cluster.local:27017)
- MONGODB_UI_DB: Database name (default: nexus)
- MONGODB_UI_COLLECTION: Collection name (default: ui_tabs)

## Document fields

Each tab is a document in the collection with the following fields:

- id (string, required): Unique identifier. Also used as tab pane id in the dashboard (e.g., "services", "grafana").
- name (string, required): Display name.
- icon (string, optional): Emoji or short label shown as an icon.
- description (string, optional): Short description shown under the name.
- enabled (bool, default: true): Set to false to hide/disable.
- type (string, default: "internal"): Either "internal" (mapped to an in-dashboard pane) or "external" (opens url in new tab).
- url (string, optional): Required if type==external. The external URL to open.
- order (int, default: 0): Sort order. Lower first; ties broken by name.
- required_groups (array[string], optional): Only show when the user belongs to at least one of these groups.
- show_on_landing (bool, default: false): If true, included in GET /api/ui/public tiles.

## Example documents

Internal Service (Services pane)
{
  "id": "services",
  "name": "Services",
  "icon": "📊",
  "description": "Manage platform services",
  "enabled": true,
  "type": "internal",
  "order": 1,
  "required_groups": ["platform-admins"],
  "show_on_landing": true
}

External Grafana
{
  "id": "grafana",
  "name": "Grafana",
  "icon": "📈",
  "description": "Monitoring dashboards",
  "enabled": true,
  "type": "external",
  "url": "http://grafana.monitoring:80",
  "order": 2,
  "required_groups": ["platform-admins", "monitoring-admin"],
  "show_on_landing": true
}

## Seeding helper

Use Mongo shell or any Mongo client to insert docs. Example using mongosh:

mongosh "mongodb://mongodb-service.default.svc.cluster.local:27017/nexus" --eval '
  db.ui_tabs.insertMany([
    { id: "services", name: "Services", icon: "📊", description: "Manage platform services", enabled: true, type: "internal", order: 1, required_groups: ["platform-admins"], show_on_landing: true },
    { id: "grafana", name: "Grafana", icon: "📈", description: "Monitoring dashboards", enabled: true, type: "external", url: "http://kube-prometheus-stack-grafana.monitoring:80", order: 2, required_groups: ["platform-admins", "monitoring-admin"], show_on_landing: true },
    { id: "prometheus", name: "Prometheus", icon: "📊", description: "Metrics explorer", enabled: true, type: "external", url: "http://kube-prometheus-stack-prometheus.monitoring:9090", order: 3, required_groups: ["platform-admins", "monitoring-admin"], show_on_landing: true },
    { id: "loki", name: "Loki", icon: "📝", description: "Centralized logging", enabled: true, type: "external", url: "http://nexus-loki.monitoring:3100", order: 4, required_groups: ["platform-admins", "monitoring-admin"], show_on_landing: false },
    { id: "databases", name: "Databases", icon: "💾", description: "Mongo Express & Orchestrators", enabled: true, type: "internal", order: 5, required_groups: ["platform-admins", "service-admin"], show_on_landing: true }
  ])
'

Note: URLs can be Service DNS for in-cluster access, or proxied paths if exposed via the admin dashboard.

## Behavior notes

- The dashboard strictly requires the Mongo collection when fetching tabs; there is no fallback.
- Landing tiles redirect to /admin?tab=<id>. After login, the requested tab is opened.
- External tabs open in a new browser tab; internal tabs map to in-dashboard panes.
