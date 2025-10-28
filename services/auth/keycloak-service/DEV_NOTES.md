Notes: HTTP vs HTTPS and Codespaces

- The development landing server (`landing-server.py`) runs a plain HTTP server (localhost) for simplicity. It listens on the port you pass (e.g. 8082) and serves files from the `services/auth/keycloak-service` directory.

- When you expose that server through GitHub Codespaces' forwarded ports or public preview, Codespaces provides HTTPS termination and a public URL like:

  https://redesigned-train-7vrwpx4wr6pfxx79-8082.app.github.dev/

  Even though the local server speaks HTTP, the Codespaces front-end will speak HTTPS to the browser and proxy to the local HTTP server. That's why the landing server prints `http://localhost:8082` locally but the public URL is `https://...`.

- The Keycloak redirect URI must match exactly what's registered in Keycloak. For Codespaces public previews we need `https://<codespace-host>-<port>.app.github.dev/` style redirect URIs.

- `config.js` was updated to force `https` for Codespaces host mapping so OIDC redirect URIs use the HTTPS scheme when running in Codespaces. If you expose the landing server with a different host or TLS setup, update `config.js` accordingly.

- For production you should run a proper TLS-terminating reverse proxy (nginx, traefik, APISIX) and use Authorization Code + PKCE for OIDC flows.
