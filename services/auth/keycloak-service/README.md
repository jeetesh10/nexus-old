Landing & Single-Sign On wiring
================================

This folder contains the static landing/login pages and small helpers for the Nexus single-sign-on demo.

Files of interest:
- `login.html` - the public landing login page. Clicking the sign-in button redirects to Keycloak (OIDC implicit flow) and returns to `router.html`.
- `router.html` - receives the id_token/access_token from Keycloak, validates state/nonce, persists tokens in sessionStorage, then redirects to `/admin/` or `/customer/` on `nexus.local`.
- `landing-page.html` - post-login landing; shows available products and a redirect banner that auto-routes by groups (configurable via `config.autoRedirectAfterLogin`).
- `switch-banner.js` - small client-side banner that can be added to any UI (admin or customer) to present a top banner that allows switching to the other portal while preserving tokens in `sessionStorage`.

How to wire everything
----------------------
1. APISIX routing (already configured)
   - `nexus.local/*` -> `landing-page-service` (landing UI)
   - `nexus.local/keycloak/*` -> `keycloak-service` (rewritten)
   - `nexus.local/admin/*` -> `admin-dashboard-service`
   - `nexus.local/customer/*` -> `customer-portal`
   - `keycloak.local/*` -> `keycloak-service` (admin console)

2. Keycloak client configuration
   - Ensure the `nexus-landing` client has redirect URIs that include `https://nexus.local/router.html` (or the exact origin you use).
   - `admin-dashboard` and `customer-portal` clients should include `https://nexus.local/admin/*` and `https://customer.local/*` as allowed redirect URIs as needed.

3. Enable the switch banner in Admin/Customer UIs
   - Copy the `switch-banner.js` file into the admin/customer UI static assets or use APISIX to inject it. Minimal example for an HTML page:

```html
<script src="/path/to/switch-banner.js"></script>
```

   - The banner checks `sessionStorage.access_token` and routes to `/admin/` or `/customer/` preserving SSO tokens.

4. Test flow
   - Open `https://nexus.local/` (or use APISIX host + `Host: nexus.local` header).
   - Click Sign In → you'll be redirected to Keycloak `nexus` realm.
   - After successful login you'll land on `router.html`, which will inspect groups and redirect you to `/admin/` or `/customer/`.
   - The admin/customer pages should include `switch-banner.js` so users can swap portals without re-login.

Notes
-----
- If you run in Codespaces or via port-forwards, replace `nexus.local` with your Codespaces URL or add the proper redirect URIs to Keycloak.
- For production you should use the Authorization Code flow (with PKCE) rather than implicit. This demo uses implicit for simplicity.
