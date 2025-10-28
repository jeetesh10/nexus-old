# RBAC Testing Guide

This guide walks through the in-cluster RBAC demo using Keycloak, Admin Dashboard, and Customer Portal.

Goals
- Seed Keycloak with the `nexus` realm, clients, groups and demo users.
- Confirm Admin Dashboard enforces the `platform-admins` group.
- Confirm Customer Portal enforces the `customers` group for `/private`.
- Demonstrate live group toggling.

Prerequisites
- A running Kubernetes cluster (kind recommended) with the platform deployed.
- `kubectl` configured to the cluster context.
- Keycloak deployed as `keycloak-service` (or reachable externally) OR you plan to run the provided seed script against an existing Keycloak.
- Seed scripts exist at `scripts/ops/seed-keycloak.sh` and `scripts/ops/keycloak-toggle-group.sh`.

Quick port-forwards (run each in a separate terminal)

```bash
# Admin Dashboard
kubectl port-forward service/admin-dashboard-service 8000:8000

# Customer Portal
kubectl port-forward service/customer-portal 8002:8002

# Keycloak (if deployed in-cluster as keycloak-service)
kubectl port-forward service/keycloak-service 8080:8080
```

1) Seed Keycloak (creates realm, clients, groups, users)

```bash
# Make the seed script executable if needed
chmod +x scripts/ops/seed-keycloak.sh

# Run the seed script
./scripts/ops/seed-keycloak.sh
```

What to expect from the seed script
- Outputs client IDs and status messages.
- Creates users `alice-admin` and `bob-customer`.
- Adds `alice-admin` to `platform-admins` and `bob-customer` to `customers`.
- Creates a `groups` claim mapper so tokens include group membership.

2) Admin Dashboard validation

- Open http://localhost:8000 in your browser (port-forward must be running).
- You should be redirected to Keycloak to authenticate.
- Sign in as `alice-admin` (seed script typically sets a known password; check the script header or logs).
- Confirm admin-only tabs are visible and that protected backend routes (for service proxying) return data.

Smoke tests (run in another terminal)

```bash
# Example: call a protected backend admin endpoint that requires admin group
curl -v --location --request GET 'http://localhost:8000/api/discovered-services' \
  --header "Authorization: Bearer <PASTE_TOKEN>"
```

3) Customer Portal validation

- Open http://localhost:8002
- The landing page should be public.
- Click Login (or navigate to the Keycloak login flow) and sign in as `bob-customer`.
- Try accessing `/private` — it should succeed when authenticated as a member of `customers` and fail/redirect otherwise.

4) Toggle group membership live

To simulate granting or revoking admin privileges to `bob-customer`:

```bash
# Grant platform-admins to bob-customer
./scripts/ops/keycloak-toggle-group.sh add bob-customer platform-admins

# Remove platform-admins from bob-customer
./scripts/ops/keycloak-toggle-group.sh remove bob-customer platform-admins
```

After toggling
- Refresh the Admin Dashboard in the browser or re-authenticate to see changes.
- For API calls, obtain a new token after a role change (Keycloak may cache tokens until next login).

Troubleshooting
- No `groups` in token: re-run seed script or create a group mapper under the client or realm token mappers to include group membership in `groups` claim.
- 401/403 from backend: confirm backend env vars (see `iac/kubernetes/*-deployment.yaml`) for `KEYCLOAK_URL`, `KEYCLOAK_REALM`, client IDs and required group names.
- Keycloak unreachable: ensure you port-forward `keycloak-service` or update `KEYCLOAK_URL` env var for apps to point to an accessible URL.
- Admin page never shows admin tabs: open browser devtools, inspect token payload (in keycloak-js it’s available on the authenticated client) and verify `groups` includes `platform-admins`.

Notes
- Tokens can be decoded at https://jwt.io for quick inspection (do not paste private tokens on public sites).
- For production, switch from public clients to confidential clients where appropriate, secure client secrets in Kubernetes secrets, and configure HTTPS.

Next steps (optional)
- Add an automated smoke test that uses the Keycloak token endpoint to obtain tokens for `alice-admin` and `bob-customer` and validates the admin/customer endpoints.
- Create a unit test in each service to validate the JWT verification middleware using a locally served JWKS JSON file.

---

Document last updated: October 18, 2025
