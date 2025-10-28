# Keycloak Quickstart

This project uses Keycloak as the identity provider. Follow these steps to ensure it's running and accessible.

## 1) Check cluster and Keycloak deployment
- Verify your k8s cluster is up: `kubectl get nodes`
- Check Keycloak resources:
  - `kubectl get deploy keycloak`
  - `kubectl get svc keycloak-service`

If missing, apply manifests: `kubectl apply -f iac/kubernetes/keycloak-deployment.yaml`

## 2) Port-forward locally (for seeding and browser)
Expose Keycloak on localhost:9080:

- `kubectl port-forward svc/keycloak-service 9080:8080`

Keep this running in a terminal while testing.

## 3) Seed realms, clients, groups, users
Seed default realms and demo users:

- Default realm `nexus`:
  - `KEYCLOAK_URL=http://localhost:9080 scripts/ops/seed-keycloak.sh`
- Optional realm `nexus-platform` (some services reference this):
  - `KEYCLOAK_URL=http://localhost:9080 KEYCLOAK_REALM=nexus-platform scripts/ops/seed-keycloak.sh`

Admin credentials used by the seed script: admin / admin.

This creates:
- Public clients: `admin-dashboard`, `customer-portal`
- Groups: `platform-admins`, `customers`
- Users: `alice-admin` (platform-admins), `bob-customer` — password: `changeme123`

## 4) Access URLs
- Direct (port-forward):
  - Realm nexus: http://localhost:9080/realms/nexus
  - Realm nexus-platform: http://localhost:9080/realms/nexus-platform
- Via APISIX gateway (single entry):
  - http://nexus.local/keycloak/ (host rule via APISIX). If you use local testing without DNS, port-forward the APISIX gateway and curl with `-H 'Host: nexus.local'`.

## 5) Service config alignment
- Admin Dashboard expects by default:
  - KEYCLOAK_REALM: `nexus`
  - KEYCLOAK_INTERNAL_URL: `http://keycloak-service:8080`
- Auth API references `nexus-platform` in some scripts. Prefer standardizing on `nexus` or set KEYCLOAK_REALM accordingly.

## 6) Troubleshooting
- Admin token fetch fails: ensure Keycloak responds: `curl -sSf http://localhost:9080/realms/master`.
- 401/403 in apps: verify group membership claim and user groups in the realm.
- CORS/redirect issues: confirm client redirect URIs and web origins in the seed script match your app URL.
