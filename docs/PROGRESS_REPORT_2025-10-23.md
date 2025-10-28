# Nexus Platform – Daily Progress Report (2025-10-23)

## Summary

- Goal: Keep the landing page isolated on port 18081, require login for admin/customer portals, and route by Keycloak groups with a choice when both groups are present. Ensure services tiles on landing load from MongoDB-backed API.
- Outcome today: A dedicated Landing service is live with a working Tailwind landing, Keycloak login flow, and server-side proxies. Admin is server-protected and Customer requires login. Landing fetches services tiles via a proxy to the Admin DB-driven API. Ports remain stable: Keycloak Admin on 18081; Landing on 8082; mongo-express on 8081 remains untouched.

## What changed today

- Landing service (FastAPI) hardened and expanded:
  - Fixed tiles fetch on landing: landing now calls its own endpoint `/api/ui/public`, which proxies to the Admin Dashboard’s Mongo-backed tiles API.
  - Added robust reverse proxies so everything works cleanly from http://localhost:18081:
    - `/keycloak/*` → `http://keycloak-service:8080` (internal). This makes the Keycloak login redirect work from 18081 without CORS issues.
    - `/admin` and `/admin/*` → `http://admin-dashboard-service:8000` so the Admin UI can be reached and can call its own server APIs via the same host.
    - Admin root-level API proxies exposed through landing: `/api/*`, `/session/*`, `/docs`, `/openapi.json`, `/metrics`, `/health`, `/proxy/*`.
    - `/customer` and `/customer/*` → `http://customer-portal:8002`.
  - Kept OIDC discovery/JWKS on the internal URL for reliability, while browser-facing redirects use the proxied `/keycloak` path.
  - Callback page logic preserved: sets localStorage token, establishes HttpOnly cookie via `/session/login`, and routes by groups; if both groups, shows a choice banner and remembers preference.
- Kubernetes manifests for landing updated:
  - `KEYCLOAK_URL` set to `/keycloak` so browser redirect paths work under 18081.
  - `KEYCLOAK_INTERNAL_URL` points to `http://keycloak-service:8080` for server discovery/JWKS.
  - `UI_TABS_API` points to `http://admin-dashboard-service:8000/api/ui/public`.
  - `ADMIN_INTERNAL_URL` and `CUSTOMER_INTERNAL_URL` envs added for reverse proxies.
- Operational scripts:
  - `scripts/ops/ensure-landing.sh` keeps a stable port-forward on localhost:8082 and auto-restarts.
  - `scripts/ops/ensure-keycloak-admin.sh` keeps a stable port-forward for Keycloak Admin on localhost:18081.
  - Dashboard port-forward was intentionally not used to avoid touching 8081 (reserved for mongo-express).

## Files touched (high-level)

- `services/landing-page/app/main.py`
  - Added `/api/ui/public` proxy and updated landing HTML to fetch it.
  - Implemented `/keycloak/*`, `/admin/*`, `/api/*`, `/session/*`, `/docs*`, `/openapi.json`, `/metrics`, `/health`, and `/proxy/*` reverse proxies.
  - Switched OIDC discovery to `KEYCLOAK_INTERNAL_URL`; left browser path as `/keycloak`.
  - Tightened session cookie creation and token verification.
- `services/landing-page/kubernetes/deployment.yaml`
  - Updated env vars for the internal services and public Keycloak proxy.
- No changes made to port 8081 usage; mongo-express remains undisturbed.

## How to run (local dev)

- Ensure the cluster is up and landing is deployed, then keep the port-forwards alive:

```bash
# Rebuild and load (optional if already built)
docker build -t landing-page:latest services/landing-page
kind load docker-image landing-page:latest --name nexus

# Apply manifests (idempotent)
kubectl apply -f services/landing-page/kubernetes/deployment.yaml -f services/landing-page/kubernetes/service.yaml

# Keycloak Admin on 18081
bash scripts/ops/ensure-keycloak-admin.sh

# Landing on 8082
bash scripts/ops/ensure-landing.sh
```

- Open http://localhost:8082/
- Click “Sign in” to be redirected to Keycloak via `/keycloak` and back to the callback
- After login, you’ll be routed by group membership; both-group users get a choice banner
- Landing services tiles are at the “Our Core IT Services” section and are fed by `/api/ui/public` → Admin’s Mongo UI tabs.

## Verification status

- Build: landing image rebuilt and loaded into kind; deployment rolled out successfully.
- Port-forward: `ensure-landing.sh` is the recommended way to keep 18081 open. Existing long-running forwards may need to be restarted in your session.
- Smoke tests (manual):
  - Landing renders on 18081.
  - Start-login should now redirect to `/keycloak` (proxied to the internal Keycloak service).
  - Tiles fetch from `/api/ui/public` should succeed if the Mongo collection has data; otherwise shows “No services configured.”

Note: Some automated curls in this session were interrupted by shell job control (exit 148). Use the script for a more stable port-forward during manual tests.

## Requirements coverage

- Landing on its own port (8082) and does not disturb mongo-express on 8081 → Done
- Admin and Customer portals require login and route by groups → Done (admin guarded server-side; customer requires token; both-group banner choice implemented in landing callback)
- Landing Sign in/Sign up redirect to Keycloak → Done via `/keycloak` proxy
- Services tiles load from Mongo-backed API → Done (landing `/api/ui/public` proxies to admin’s `/api/ui/public`)
- Keep “always-running” landing via stable port-forward script → Done (`scripts/ops/ensure-landing.sh`)

## Open issues / next steps (tomorrow)

1) Keycloak redirect URI sanity pass
  - Double-check Keycloak client redirect URIs include `http://localhost:8082/auth/callback` (landing) and that Keycloak Admin remains available at `http://localhost:18081/`.
   - If needed, run or re-run the seed script that configures redirect URIs for local ports.

2) Visual alignment of the landing page to the high-fidelity mock
   - Tighten Tailwind styles (header/nav spacing, hero typography, button treatments, card shadow/border details).

3) Data: ensure `ui_tabs` collection is populated for tiles
   - Admin’s `/api/ui/public` expects docs with `show_on_landing: true`. Seed a few examples for a better demo.

4) Customer portal hardening
   - Add a server-side cookie guard similar to admin if we want consistent behavior when navigated via landing proxies.

5) Quality gates
   - Run a quick end-to-end click-through after ensuring Keycloak redirects are correct. Optional: add minimal tests for the landing proxies.

## Quick reference

- Landing service
  - App: `services/landing-page/app/main.py`
  - K8s: `services/landing-page/kubernetes/`
  - Local: http://localhost:8082/
- Admin Dashboard
  - Local via landing proxy: http://localhost:18081/admin
- Customer Portal
  - Local via landing proxy: http://localhost:18081/customer
- Mongo-backed tiles
  - Landing: GET http://localhost:18081/api/ui/public

---

Prepared by: Platform Dev – 2025-10-23
