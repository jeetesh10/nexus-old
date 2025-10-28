# Customer Portal

A minimal FastAPI service that serves a public landing page and health endpoint. Intended to be exposed publicly and gated by Keycloak for authenticated areas in the future.

- Port: 8002
- Endpoints:
  - GET /health
  - GET /

## Run locally

```bash
uvicorn app.main:app --reload --port 8002
```

## Kubernetes

Apply the manifest:

```bash
kubectl apply -f iac/kubernetes/customer-portal-deployment.yaml
```