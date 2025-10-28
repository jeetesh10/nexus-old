# Development Guidelines — Linkerd, APISIX, MongoOrchestrator

Purpose
- Provide clear, actionable guidance for when and how to use Linkerd (service mesh), APISIX (API gateway/ingress) and MongoOrchestrator (MongoDB HTTP adapter/orchestrator) during development, testing and production deployment.

Audience
- Service developers, SREs, and CI authors working in this repo.

Contents
1. Principles
2. MongoOrchestrator: when & how to use
3. Linkerd (service mesh): when & how to use
4. APISIX (API gateway/ingress): when & how to use
5. How these components must be wired together
6. Files-of-truth, templating and CI
7. Debugging and common commands
8. Checklist before deploy

---

1. Principles
- Keep a single source-of-truth for cross-cutting config (ports, service names, ingress hosts) in `config/ports.yaml`.
- Prefer configuration-as-code and render manifests in CI (Helm / Kustomize / yq / envsubst).
- Use service-local DNS names for in-cluster communication (e.g., `mongodb-orchestrator.default.svc.cluster.local`).
- Do not hardcode secrets into manifests. Use Kubernetes Secrets and reference them as env or volume mounts.

2. MongoOrchestrator
When to use
- Use MongoOrchestrator where a lightweight HTTP façade is needed for CRUD, configuration, or to centralize DB access patterns.
- Use it in dev and test to avoid direct DB access from many services and to centralize migrations, seeding and access control rules.

How to run
- Image listens on container port defined in `config/ports.yaml` (example: containerPort 8080; servicePort often 80).
- Config is provided via `ConfigMap` keys: `MONGO_URI` (or `MONGODB_URL`), `MONGO_DB`, `PORT`.
- Ensure `MONGO_URI` points to the cluster Mongo service (e.g. `mongodb-service.default.svc.cluster.local:27017`) and includes `authSource` if required.

Health & probes
- Health path: `/health` (should return 200 JSON).
- Set liveness/readiness probes to the same port as `containerPort`.

Common issues
- CrashLoopBackOff often results from wrong DB URL or missing credentials. Check logs for "Connection refused" / "ping failed".
- If app still attempts `localhost:27017`, identify which env var the app reads and set it (ConfigMap or env).

3. Linkerd (service mesh)
When to use
- Use Linkerd for mTLS, observability, traffic policy, and lightweight service-to-service metrics.
- Use in staging and production. Optional in local dev — enable only when needed.

How to use
- Injection via annotation: `linkerd.io/inject: enabled` on Pod template metadata.
- Ensure deployments reference a ServiceAccount if Linkerd policies require one.
- Do not modify container networking logic — Linkerd sidecar expects the app to bind to 0.0.0.0 and probe ports to be accurate.

Common gotchas
- Linkerd may surface "Connection refused" from proxy when the app crashes early. Always fix app crash first.
- When patching deployments, do NOT remove the `image` field in the container spec — kubectl merge patches can break validation.
- To disable injection temporarily for debugging:
  kubectl annotate deploy <name> linkerd.io/inject- --overwrite

4. APISIX (API gateway / ingress)
When to use
- Use APISIX as the ingress for external traffic, routing, authentication (JWT), rate-limiting, and observability at the edge.
- Use APISIX to centralize external concerns and keep internal services simple.

How to use
- Create APISIX routes that map external paths/hosts to in-cluster services (service name + port).
- Offload TLS to APISIX or the cloud LB. Use APISIX plugins for JWT, rate-limiting and IP allowlists.

Example route snippet (conceptual)
- Upstream: `mongodb-orchestrator` service, port = servicePort from `config/ports.yaml`.
- Route: host = `mongodb-orchestrator.local`, path prefix `/api/v1/*`, plugin = auth/rate-limit as needed.

5. Wiring these components
- Internal services call MongoOrchestrator via in-cluster DNS: `http://mongodb-orchestrator.default.svc.cluster.local:<servicePort>`.
- APISIX exposes the orchestrator externally (if needed) using an ingress route to the service port.
- Linkerd sits between services; traffic flows app -> Linkerd sidecar -> destination sidecar -> app. APISIX gateway usually sits outside the mesh (edge), unless you explicitly inject it.

6. Files-of-truth, templating and CI
- Ports: `config/ports.yaml` must be the canonical source for containerPort / servicePort / ingressHost.
- Ports file (config/ports.yaml)
- The canonical ports file is `config/ports.yaml`. Every service must have an entry with at least:
  - containerPort: port the container listens on
  - servicePort: port the Kubernetes Service exposes (optional)
  - ingressHost: optional host used by APISIX / local testing
- Update `config/ports.yaml` before changing any Dockerfile CMD, container CMD ports or Kubernetes manifests. Treat it as the single source-of-truth.

Enforcing config/ports.yaml usage
- A repository validator (`scripts/validate-ports.sh`) checks that manifests in common IaC folders reference the ports declared in `config/ports.yaml`.
- A GitHub Actions job (`.github/workflows/validate-ports.yml`) runs the validator on PRs and will fail the check if a declared containerPort is not found in the IaC manifests.
- Local workflow:
  1. Edit `config/ports.yaml` first for any port change.
  2. Run `./scripts/validate-ports.sh` locally and fix any errors.
  3. Update templated manifests (Helm values, Kustomize or raw YAML) and open a PR. CI will validate ports and block merges on mismatches.

Biasing Copilot and automation
- Copilot uses repository context. To encourage correct suggestions:
  - Keep `config/ports.yaml`, `docs/development-guidelines.md`, and `scripts/validate-ports.sh` present and up-to-date.
  - Provide manifest templates and examples that reference `config/ports.yaml` values (Helm values or placeholders).
  - CI enforces correctness: if Copilot suggests a manifest that drifts from `config/ports.yaml`, the PR check fails and the developer must correct it.
- Recommended CI policy:
  - Treat containerPort mismatches as blocking (ERROR).
  - Treat servicePort missing matches as WARN (adjust in validator if you prefer strictness).

Quick developer workflow (one-liner)
1. Update ports: edit `config/ports.yaml`.
2. Validate locally: `chmod +x scripts/validate-ports.sh && ./scripts/validate-ports.sh`.
3. Update manifests/templates to use the new port.
4. Open PR — CI runs validation.

Automation suggestion
- Prefer Helm/Kustomize to inject values from `config/ports.yaml` at render time.
- If you cannot use Helm/Kustomize yet, add a small templating step in CI to substitute ports into manifests (using `yq` or `envsubst`) before applying.

Debugging note
- If a service fails due to port mismatch, validator + CI will catch it early. For runtime issues, use:
  - `kubectl -n default get pods -l app=<service> -o wide`
  - `kubectl -n default logs <pod> -c <container> --tail=200`
  - `kubectl -n default describe pod <pod>`

Keep this document updated as the architecture evolves. For automation help (Helm chart or Kustomize generator) open an issue and include target environments.