import os
from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, Response, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
if TYPE_CHECKING:
    # runtime kubernetes client imported only for type checkers when available
    from kubernetes import client, config  # type: ignore
else:
    # import at runtime (may not be available in some dev environments)
    try:
        from kubernetes import client, config  # type: ignore
    except Exception:
        client = None  # type: ignore
        config = None  # type: ignore
import json
from urllib.parse import quote_plus
from datetime import datetime, timezone
import time
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.registry import REGISTRY
from jose import jwt, JWTError
from cachetools import TTLCache
import asyncio
from functools import lru_cache

# Optional Mongo audit (Motor)
try:
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
except Exception:
    AsyncIOMotorClient = None  # type: ignore

# OIDC / Keycloak config via env
# Public URL used by browsers (can be relative like '/keycloak' for Codespaces)
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_URL", "/keycloak")
# Internal URL used by the server to reach Keycloak (cluster service)
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak-service:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "nexus")
ADMIN_CLIENT_ID = os.getenv("ADMIN_CLIENT_ID", "admin-dashboard")
CUSTOMER_CLIENT_ID = os.getenv("CUSTOMER_CLIENT_ID", "customer-portal")
REQUIRED_ADMIN_GROUP = os.getenv("REQUIRED_ADMIN_GROUP", "platform-admins")
REQUIRED_CUSTOMER_GROUP = os.getenv("REQUIRED_CUSTOMER_GROUP", "customers")

# Optional direct proxy targets for common UIs
APISIX_DASHBOARD_URL = os.getenv("APISIX_DASHBOARD_URL", "http://apisix-dashboard.apisix.svc.cluster.local:9000")
KAFKA_UI_URL = os.getenv("KAFKA_UI_URL", "http://kafka-ui.kafka.svc.cluster.local:8080")

OIDC_DISCOVERY = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
jwks_uri: Optional[str] = None
_issuer_discovered: Optional[str] = None
_jwks_cache: TTLCache[str, Any] = TTLCache(maxsize=1, ttl=300)

# Optional audit store
MONGODB_AUDIT_URI = os.getenv("MONGODB_AUDIT_URI")
_audit_client = None
_audit_coll = None

async def _get_jwks() -> Dict[str, Any]:
    global jwks_uri
    if "jwks" in _jwks_cache:
        return _jwks_cache["jwks"]
    async with httpx.AsyncClient(timeout=10.0) as c:
        # discover JWKS URI once
        if jwks_uri is None:
            r = await c.get(OIDC_DISCOVERY)
            r.raise_for_status()
            data = r.json()
            jwks_uri = data.get("jwks_uri")
            # cache issuer from discovery for JWT validation
            global _issuer_discovered
            _issuer_discovered = data.get("issuer") or _issuer_discovered
        if not jwks_uri:
            raise RuntimeError("Could not determine JWKS URI from OIDC discovery")
        r2 = await c.get(jwks_uri)
        r2.raise_for_status()
        jwks = r2.json()
        _jwks_cache["jwks"] = jwks
        return jwks
async def verify_jwt(request: Request, required_group: Optional[str] = None) -> Dict[str, Any]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1]
    try:
        jwks = await _get_jwks()
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="No matching JWKS key")
        # Prefer discovered issuer. If not available, skip issuer verification
        options = {"verify_aud": False}
        issuer = _issuer_discovered
        try:
            if issuer:
                payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options, issuer=issuer)
            else:
                options["verify_iss"] = False
                payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options)
        except JWTError:
            # Fallback: skip issuer verification to tolerate proxy/public vs internal issuer differences
            options["verify_iss"] = False
            payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options)
        # group check
        if required_group:
            groups = payload.get("groups", [])
            if required_group not in groups:
                raise HTTPException(status_code=403, detail="Insufficient group membership")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def verify_jwt_token(token: str, required_group: Optional[str] = None) -> Dict[str, Any]:
    """Verify a JWT provided directly (e.g., from cookie)."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        jwks = await _get_jwks()
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="No matching JWKS key")
        options = {"verify_aud": False}
        issuer = _issuer_discovered
        try:
            if issuer:
                payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options, issuer=issuer)
            else:
                options["verify_iss"] = False
                payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options)
        except JWTError:
            options["verify_iss"] = False
            payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options=options)
        if required_group:
            groups = payload.get("groups", [])
            if required_group not in groups:
                raise HTTPException(status_code=403, detail="Insufficient group membership")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def ensure_admin(request: Request):
    await verify_jwt(request, required_group=REQUIRED_ADMIN_GROUP)

async def ensure_customer(request: Request):
    await verify_jwt(request, required_group=REQUIRED_CUSTOMER_GROUP)

app = FastAPI()

# Kubernetes client will be configured at startup if available
from typing import Any as _Any, cast
v1: _Any = None
k8s_enabled = False
try:
    if config is not None:
        config.load_incluster_config()  # type: ignore[attr-defined]
        v1 = client.AppsV1Api()  # type: ignore[attr-defined]
        k8s_enabled = True
except Exception:
    try:
        if config is not None:
            config.load_kube_config()  # type: ignore[attr-defined]
            v1 = client.AppsV1Api()  # type: ignore[attr-defined]
            k8s_enabled = True
    except Exception:
        print("[WARN] Could not configure Kubernetes client, running in mock mode.")
        v1 = None
        k8s_enabled = False

# Initialize optional audit Mongo client
_audit_client: _Any = None
_audit_coll: _Any = None
if MONGODB_AUDIT_URI and AsyncIOMotorClient is not None:
    try:
        _audit_client = cast(_Any, AsyncIOMotorClient(MONGODB_AUDIT_URI))
        # database name can be in URI; default to 'nexus' if none, and collection 'audit_logins'
        # Motor derives DB from URI; for safety, allow env MONGODB_AUDIT_DB/COLL override
        AUDIT_DB = os.getenv("MONGODB_AUDIT_DB", "nexus")
        AUDIT_COLL = os.getenv("MONGODB_AUDIT_COLLECTION", "audit_logins")
        _audit_coll = _audit_client[AUDIT_DB][AUDIT_COLL]
    except Exception as e:
        print(f"[WARN] Audit Mongo init failed: {e}")
        _audit_client = None
        _audit_coll = None

# Optional UI tabs config store (data-driven navigation)
MONGODB_UI_URI = os.getenv("MONGODB_UI_URI", MONGODB_AUDIT_URI or "")
MONGODB_UI_DB = os.getenv("MONGODB_UI_DB", os.getenv("MONGODB_AUDIT_DB", "nexus"))
MONGODB_UI_COLLECTION = os.getenv("MONGODB_UI_COLLECTION", "ui_tabs")
_ui_client: _Any = None
_ui_coll: _Any = None
if MONGODB_UI_URI and AsyncIOMotorClient is not None:
    try:
        _ui_client = cast(_Any, AsyncIOMotorClient(MONGODB_UI_URI))
        _ui_coll = _ui_client[MONGODB_UI_DB][MONGODB_UI_COLLECTION]
    except Exception as e:
        print(f"[WARN] UI Tabs Mongo init failed: {e}")
        _ui_client = None
        _ui_coll = None

async def _audit_event(payload: Dict[str, Any], event_type: str = "whoami", request: Optional[Request] = None) -> None:
    if _audit_coll is None:
        return
    try:
        doc: Dict[str, Any] = {
            "event_type": event_type,
            "at": datetime.now(timezone.utc).isoformat(),
            "sub": payload.get("sub"),
            "preferred_username": payload.get("preferred_username"),
            "email": payload.get("email"),
            "groups": payload.get("groups", []),
            "client_id": payload.get("azp") or payload.get("clientId"),
            "iss": payload.get("iss"),
            "aud": payload.get("aud"),
            "source": "admin-dashboard",
        }
        if request is not None:
            doc["ip"] = request.client.host if request.client else None
            doc["path"] = str(request.url)
            doc["user_agent"] = request.headers.get("user-agent")
        await _audit_coll.insert_one(doc)
    except Exception as e:
        print(f"[WARN] audit write failed: {e}")

def _normalize_groups(groups: list[str]) -> set[str]:
    out: set[str] = set()
    for g in groups or []:
        lg = str(g).strip().lower()
        if not lg:
            continue
        out.add(lg)
        if lg.endswith('s'):
            out.add(lg[:-1])
    # common synonyms
    out.update({"platform-admin", "platform-admins", "admin", "admins", "customer", "customers"})
    return out

def _is_in_groups(user_groups: list[str], required: str) -> bool:
    if not required:
        return True
    norm = _normalize_groups(user_groups)
    r = required.strip().lower()
    return r in norm or (r.endswith('s') and r[:-1] in norm) or (r + 's' in norm)

def _normalized_origin(request: Request) -> str:
    """Best-effort origin using X-Forwarded-* headers for proxied environments like Codespaces."""
    xf_proto = (request.headers.get("x-forwarded-proto", "").split(",")[0] or "").strip()
    xf_host = (request.headers.get("x-forwarded-host", "").split(",")[0] or "").strip()
    scheme = xf_proto or (request.url.scheme or "http")
    host = xf_host or request.headers.get("host") or "localhost"
    if host.endswith(":443"):
        host = host[:-4]
    if host.endswith(":80"):
        host = host[:-3]
    return f"{scheme}://{host}"

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_services = Gauge('active_services', 'Number of active services')
total_services = Gauge('total_services', 'Total number of services')


@app.get("/api/ui/tabs")
async def get_ui_tabs(request: Request, _: Dict[str, Any] = Depends(ensure_admin)):
    """Return the list of UI tabs for the current user, sourced strictly from Mongo collection.
    Filters by required_groups if present. Tabs support fields: id, name, icon, description,
    type (internal|external), url (for external), order, enabled, required_groups.
    """
    # Extract user groups from JWT cookie (best-effort)
    user_groups: list[str] = []
    try:
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            payload = await verify_jwt_token(token_cookie)
            user_groups = list(payload.get("groups", []) or [])
    except Exception:
        user_groups = []
    # Always include admin group so platform-admins see all admin tabs by default
    if REQUIRED_ADMIN_GROUP not in user_groups:
        user_groups.append(REQUIRED_ADMIN_GROUP)
    tabs: list[dict[str, Any]] = []
    if _ui_coll is None:
        raise HTTPException(status_code=500, detail="UI tabs store not configured (set MONGODB_UI_URI)")
    try:
        cursor = _ui_coll.find({"enabled": {"$ne": False}}).sort([("order", 1), ("name", 1)])
        docs = await cursor.to_list(length=500)
        for d in docs:
            raw_req = d.get("required_groups") or []
            if not isinstance(raw_req, list):
                raw_req = []
            req = [str(x) for x in raw_req]  # type: ignore
            if req and not any((str(g) in user_groups) for g in req):
                continue
            tabs.append({
                "id": d.get("id"),
                "name": d.get("name"),
                "icon": d.get("icon", "📁"),
                "description": d.get("description", ""),
                "enabled": d.get("enabled", True),
                "type": d.get("type", "internal"),
                "url": d.get("url"),
                "order": d.get("order", 0),
                "required_groups": req,
            })
        tabs.sort(key=lambda x: (int(x.get("order", 0)), str(x.get("name", ""))))
        return {"tabs": tabs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ui/public")
async def get_public_tabs():
    """Public endpoint for landing page tiles. No fallback—purely DB-driven.
    Expected doc fields:
      - id (string)
      - name (string) -> exposed as title
      - description (string)
      - icon (string, optional) inner SVG paths/lines markup to render
      - color (string, optional) hex color used for accent
      - info_url (string, optional) -> exposed as infoPageUrl
      - service_url (string, optional) -> exposed as servicePageUrl
      - enabled (bool), order (number), show_on_landing (bool)
    """
    if _ui_coll is None:
        raise HTTPException(status_code=500, detail="UI tabs store not configured (set MONGODB_UI_URI)")
    try:
        cursor = _ui_coll.find({
            "enabled": {"$ne": False},
            "show_on_landing": True
        }).sort([("order", 1), ("name", 1)])
        docs = await cursor.to_list(length=500)
        out = [{
            "id": d.get("id"),
            "title": d.get("name") or d.get("id"),
            "description": d.get("description", ""),
            "color": d.get("color"),
            "icon": d.get("icon"),
            "infoPageUrl": d.get("info_url"),
            "servicePageUrl": d.get("service_url"),
            "order": d.get("order", 0),
        } for d in docs]
        return {"tabs": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    # Server-side auth guard: require a valid admin token in HttpOnly cookie
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        return RedirectResponse(url="/start-login")
    try:
        await verify_jwt_token(token_cookie, REQUIRED_ADMIN_GROUP)
    except HTTPException:
        return RedirectResponse(url="/start-login")
    start_time = time.time()
    """Main dashboard with vertical tabs for all services"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            .dashboard-container {
                display: flex;
                min-height: 100vh;
            }
            
            .main-content {
                flex: 1;
                padding: 20px;
                margin-left: 280px;
                transition: margin-left 0.3s ease;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-left {
                text-align: left;
            }
            
            .header h1 {
                color: #4a5568;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #718096;
                font-size: 16px;
            }
            
            .user-profile {
                position: relative;
            }
            
            .user-avatar {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
            
            .user-avatar:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .avatar-icon {
                font-size: 24px;
                color: white;
            }
            
            .user-dropdown {
                position: absolute;
                top: 60px;
                right: 0;
                width: 280px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                border: 1px solid #e2e8f0;
                opacity: 0;
                visibility: hidden;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                z-index: 1000;
            }
            
            .user-dropdown.show {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }
            
            .user-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .user-avatar-small {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: white;
            }
            
            .user-details {
                flex: 1;
            }
            
            .user-name {
                font-weight: 600;
                color: #2d3748;
                font-size: 16px;
                margin-bottom: 2px;
            }
            
            .user-role {
                color: #718096;
                font-size: 12px;
                background: #f7fafc;
                padding: 2px 8px;
                border-radius: 12px;
                display: inline-block;
            }
            
            .user-menu-items {
                padding: 8px 0;
            }
            
            .menu-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 20px;
                cursor: pointer;
                transition: background-color 0.2s ease;
                color: #4a5568;
                font-size: 14px;
            }
            
            .menu-item:hover {
                background-color: #f7fafc;
            }
            
            .menu-icon {
                font-size: 16px;
                width: 20px;
                text-align: center;
            }
            
            .menu-divider {
                height: 1px;
                background: #e2e8f0;
                margin: 8px 0;
            }
            
            .logout-item {
                color: #e53e3e;
            }
            
            .logout-item:hover {
                background-color: #fed7d7;
            }
            
            .logout-btn-fallback {
                background: #e53e3e;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                margin-left: 10px;
                transition: all 0.2s ease;
            }
            
            .logout-btn-fallback:hover {
                background: #c53030;
                transform: translateY(-1px);
            }
            
            .user-info {
                position: absolute;
                top: 20px;
                left: 300px;
                background: rgba(255, 255, 255, 0.9);
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 14px;
                color: #4a5568;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .sidebar {
                position: fixed;
                left: 0;
                top: 0;
                width: 280px;
                height: 100vh;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                box-shadow: 4px 0 6px rgba(0, 0, 0, 0.1);
                overflow-y: auto;
                z-index: 1000;
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                text-align: center;
            }
            
            .sidebar-header h3 {
                color: #4a5568;
                font-size: 18px;
                margin-bottom: 5px;
            }
            
            .sidebar-header p {
                color: #718096;
                font-size: 12px;
            }
            
            .tabs-container {
                padding: 10px;
            }
            
            .tab {
                display: flex;
                align-items: center;
                padding: 15px;
                margin: 5px 0;
                background: transparent;
                border: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #4a5568;
                transition: all 0.3s ease;
                border-radius: 8px;
                width: 100%;
                text-align: left;
                position: relative;
            }
            
            .tab:hover {
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                transform: translateX(5px);
            }
            
            .tab.active {
                background: rgba(102, 126, 234, 0.15);
                color: #667eea;
                box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
            }
            
            .tab-icon {
                font-size: 18px;
                margin-right: 12px;
                width: 24px;
                text-align: center;
            }
            
            .tab-content {
                flex: 1;
            }
            
            .tab-name {
                font-weight: 600;
                margin-bottom: 2px;
            }
            
            .tab-description {
                font-size: 11px;
                color: #718096;
                opacity: 0.8;
            }
            
            .tab.disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .tab.disabled:hover {
                transform: none;
                background: transparent;
            }
            
            .content-area {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                padding: 30px;
                min-height: 600px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .tab-pane {
                display: none;
            }
            
            .tab-pane.active {
                display: block;
            }
            
            .service-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .service-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #667eea;
                transition: transform 0.2s ease;
            }
            
            .service-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            
            .service-name {
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 5px;
            }
            
            .service-namespace {
                color: #718096;
                font-size: 12px;
                margin-bottom: 10px;
            }
            
            .service-status {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                margin-bottom: 15px;
            }
            
            .status-running {
                background: #c6f6d5;
                color: #22543d;
            }
            
            .status-stopped {
                background: #fed7d7;
                color: #742a2a;
            }
            
            .service-actions {
                display: flex;
                gap: 10px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
            }
            
            .btn-primary {
                background: #667eea;
                color: white;
            }
            
            .btn-primary:hover {
                background: #5a67d8;
            }
            
            .btn-danger {
                background: #e53e3e;
                color: white;
            }
            
            .btn-danger:hover {
                background: #c53030;
            }
            
            .btn-success {
                background: #38a169;
                color: white;
            }
            
            .btn-success:hover {
                background: #2f855a;
            }
            
            .btn-secondary {
                background: #718096;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #4a5568;
            }
            
            .iframe-container {
                width: 100%;
                height: 600px;
                border: none;
                border-radius: 8px;
                background: white;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #718096;
            }
            
            .error {
                background: #fed7d7;
                color: #742a2a;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }
            
            .refresh-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                margin-bottom: 20px;
            }
            
            .refresh-btn:hover {
                background: #5a67d8;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .stat-label {
                color: #718096;
                font-size: 14px;
            }
            
            .chart-container {
                width: 100%;
                height: 200px;
                margin-top: 15px;
            }
            
            .mini-chart {
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-radius: 6px;
                position: relative;
                overflow: hidden;
            }
            
            .chart-bar {
                position: absolute;
                bottom: 0;
                background: linear-gradient(to top, #667eea, #764ba2);
                border-radius: 2px 2px 0 0;
                transition: height 0.3s ease;
            }
            
            .chart-line {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: #667eea;
                transform-origin: left;
                animation: chartGrow 2s ease-out;
            }
            
            @keyframes chartGrow {
                from { transform: scaleX(0); }
                to { transform: scaleX(1); }
            }
            
            .coming-soon {
                text-align: center;
                padding: 60px 20px;
                color: #718096;
            }
            
            .coming-soon h2 {
                margin-bottom: 10px;
                color: #4a5568;
            }
            
            .coming-soon p {
                margin-bottom: 20px;
            }
            
            .role-badge {
                display: inline-block;
                padding: 2px 8px;
                background: #667eea;
                color: white;
                border-radius: 12px;
                font-size: 10px;
                margin-left: 10px;
            }
            
            @media (max-width: 768px) {
                .main-content {
                    margin-left: 0;
                    padding: 10px;
                }
                
                .sidebar {
                    transform: translateX(-100%);
                    transition: transform 0.3s ease;
                }
                
                .sidebar.open {
                    transform: translateX(0);
                }
                
                .mobile-toggle {
                    display: block;
                    position: fixed;
                    top: 20px;
                    left: 20px;
                    z-index: 1001;
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 50%;
                    cursor: pointer;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="main-content">
                <div class="header">
                    <div class="header-left">
                        <h1>🚀 Nexus Admin Dashboard</h1>
                        <p>Unified management interface for your Kubernetes platform</p>
                    </div>
                    <div class="user-profile">
                        <div class="user-avatar" onclick="toggleUserMenu()">
                            <span class="avatar-icon">👤</span>
                        </div>
                        <div class="user-dropdown" id="user-dropdown">
                            <div class="user-header">
                                <div class="user-avatar-small">👤</div>
                                <div class="user-details">
                                    <div class="user-name" id="current-user">Platform Admin</div>
                                    <div class="user-role" id="current-role">platform-admin</div>
                                </div>
                            </div>
                            <div class="user-menu-items">
                                <div class="menu-item" onclick="showUserProfile()">
                                    <span class="menu-icon">👤</span>
                                    <span>Profile</span>
                                </div>
                                <div class="menu-item" onclick="showUserSettings()">
                                    <span class="menu-icon">⚙️</span>
                                    <span>Settings</span>
                                </div>
                                <div class="menu-divider"></div>
                                <div class="menu-item logout-item" onclick="logout()">
                                    <span class="menu-icon">🚪</span>
                                    <span>Logout</span>
                                </div>
                            </div>
                        </div>
                        <!-- Fallback logout button for better visibility -->
                        <button class="logout-btn-fallback" onclick="logout()" title="Logout">
                            🚪 Logout
                        </button>
                    </div>
                </div>
                
                <div class="content-area">
                    <!-- Services Tab -->
                    <div id="services" class="tab-pane active">
                        <button class="refresh-btn" onclick="loadServices()">🔄 Refresh Services</button>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number" id="total-services">-</div>
                                <div class="stat-label">Total Services</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-bar" id="total-chart" style="width: 20%; height: 0%; left: 10%;"></div>
                                        <div class="chart-bar" id="total-chart2" style="width: 20%; height: 0%; left: 40%;"></div>
                                        <div class="chart-bar" id="total-chart3" style="width: 20%; height: 0%; left: 70%;"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="running-services">-</div>
                                <div class="stat-label">Running</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-line" id="running-chart" style="transform: scaleX(0);"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number" id="stopped-services">-</div>
                                <div class="stat-label">Stopped</div>
                                <div class="chart-container">
                                    <div class="mini-chart">
                                        <div class="chart-bar" id="stopped-chart" style="width: 30%; height: 0%; left: 35%;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="services-container" class="service-grid">
                            <div class="loading">Loading services...</div>
                        </div>
                    </div>
                    
                    <!-- Grafana Tab -->
                    <div id="grafana" class="tab-pane">
                        <h2>📈 Grafana Dashboard</h2>
                        <p>Access your monitoring dashboards and visualizations.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:3000" target="_blank" class="btn btn-secondary">Open Grafana in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshGrafana()">🔄 Refresh</button>
                        </div>
                        <div id="grafana-loading" class="loading" style="display: none;">
                            <p>Loading metrics...</p>
                        </div>
                        <div id="grafana-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Quick Metrics Overview</h3>
                                <div id="metrics-overview" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="cpu-usage" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">CPU Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="memory-usage" style="font-size: 2em; color: #ffd93d;">-</div>
                                        <div style="color: #888;">Memory Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="pod-count" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Running Pods</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="service-count" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Active Services</div>
                                    </div>
                                </div>
                            </div>
                            <div style="text-align: center; padding: 20px;">
                                <p style="color: #888; margin-bottom: 15px;">For detailed dashboards and advanced visualizations:</p>
                                <a href="http://localhost:3000" target="_blank" class="btn btn-primary">Open Full Grafana Dashboard</a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Prometheus Tab -->
                    <div id="prometheus" class="tab-pane">
                        <h2>📊 Prometheus Metrics</h2>
                        <p>View metrics and configure alerting rules.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:9090" target="_blank" class="btn btn-secondary">Open Prometheus in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshPrometheus()">🔄 Refresh</button>
                        </div>
                        <div id="prometheus-loading" class="loading" style="display: none;">
                            <p>Loading metrics...</p>
                        </div>
                        <div id="prometheus-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Key Metrics Overview</h3>
                                <div id="prometheus-metrics" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="up-services" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Services Up</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="cpu-usage-prom" style="font-size: 2em; color: #ffd93d;">-</div>
                                        <div style="color: #888;">CPU Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="memory-usage-prom" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Memory Usage</div>
                                    </div>
                                    <div style="background: #2d2d2d; padding: 15px; border-radius: 6px; text-align: center;">
                                        <div id="request-rate" style="font-size: 2em; color: #6bcf7f;">-</div>
                                        <div style="color: #888;">Request Rate</div>
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 20px;">
                                <h4>Quick Queries:</h4>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                                    <button class="btn btn-secondary" onclick="queryPrometheus('up')">Services Status</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('node_cpu_seconds_total')">CPU Metrics</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('container_memory_usage_bytes')">Memory Metrics</button>
                                    <button class="btn btn-secondary" onclick="queryPrometheus('http_requests_total')">HTTP Requests</button>
                                </div>
                                <div id="prometheus-query-result" style="margin-top: 15px; background: #f5f5f5; padding: 15px; border-radius: 6px; font-family: monospace; display: none;">
                                    <div id="query-result-content"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Loki Tab -->
                    <div id="loki" class="tab-pane">
                        <h2>📝 Loki Logs</h2>
                        <p>Query and view centralized logs.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:3100" target="_blank" class="btn btn-secondary">Open Loki in New Tab</a>
                            <button class="btn btn-secondary" onclick="refreshLoki()">🔄 Refresh</button>
                        </div>
                        <div id="loki-loading" class="loading" style="display: none;">
                            <p>Loading logs...</p>
                        </div>
                        <div id="loki-content">
                            <div style="background: #1e1e1e; color: #fff; padding: 20px; border-radius: 8px; font-family: monospace; height: 500px; overflow-y: auto;">
                                <h3 style="color: #00ff00; margin-bottom: 15px;">📊 Live Log Stream</h3>
                                <div id="log-stream" style="line-height: 1.6;">
                                    <div style="color: #888;">Loading logs...</div>
                                </div>
                            </div>
                            <div style="margin-top: 20px;">
                                <h4>Quick Queries:</h4>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                                    <button class="btn btn-secondary" onclick="queryLogs('{app=\"log-generator\"}')">Log Generator</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{app=\"sample-webapp\"}')">Sample WebApp</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{level=\"ERROR\"}')">Error Logs</button>
                                    <button class="btn btn-secondary" onclick="queryLogs('{level=\"WARN\"}')">Warning Logs</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Alertmanager Tab -->
                    <div id="alertmanager" class="tab-pane">
                        <h2>🚨 Alertmanager</h2>
                        <p>Manage alerts and notification routing.</p>
                        <div style="margin: 20px 0;">
                            <a href="http://localhost:9093" target="_blank" class="btn btn-primary">Open Alertmanager in New Tab</a>
                        </div>
                        <iframe src="http://localhost:9093" class="iframe-container" id="alertmanager-iframe"></iframe>
                    </div>

                    <!-- APISIX Tab -->
                    <div id="apisix" class="tab-pane">
                        <h2>🛣️ APISIX Dashboard</h2>
                        <p>Reverse proxy and API gateway management UI.</p>
                        <div style="margin: 16px 0; display: flex; gap: 10px; flex-wrap: wrap;">
                            <a href="/proxy/apisix/" class="btn btn-primary" target="_blank">Open APISIX (new tab)</a>
                            <button class="btn btn-secondary" onclick="loadApisix()">Open Inline</button>
                        </div>
                        <iframe id="apisix-iframe" class="iframe-container" style="display:none;" src=""></iframe>
                    </div>

                    <!-- Kafka UI Tab -->
                    <div id="kafka-ui" class="tab-pane">
                        <h2>📬 Kafka UI</h2>
                        <p>Manage topics, partitions, and consumer groups.</p>
                        <div style="margin: 16px 0; display: flex; gap: 10px; flex-wrap: wrap;">
                            <a href="/proxy/kafka-ui/" class="btn btn-primary" target="_blank">Open Kafka UI (new tab)</a>
                            <button class="btn btn-secondary" onclick="loadKafkaUI()">Open Inline</button>
                        </div>
                        <iframe id="kafka-iframe" class="iframe-container" style="display:none;" src=""></iframe>
                    </div>
                    
                    <!-- Keycloak Tab -->
                    <div id="keycloak" class="tab-pane">
                        <div class="coming-soon">
                            <h2>🔐 Keycloak Admin Console</h2>
                            <p>To avoid browser CSP and frame restrictions, the Keycloak console opens in a new tab.</p>
                            <div style="margin: 20px 0;">
                                <a href="/keycloak/" target="_blank" class="btn btn-primary">Open Keycloak in New Tab</a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- API Tab -->
                    <div id="api" class="tab-pane">
                        <h2>🔧 API Documentation</h2>
                        <p>Test the admin dashboard API endpoints directly.</p>
                        <div style="margin: 20px 0;">
                            <a href="/docs" target="_blank" class="btn btn-primary">Open API Docs</a>
                        </div>
                        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3>Available Endpoints:</h3>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>GET /api/services</strong> - List all services</li>
                                <li><strong>POST /api/services/{name}/stop</strong> - Stop a service</li>
                                <li><strong>POST /api/services/{name}/start</strong> - Start a service</li>
                                <li><strong>GET /health</strong> - Health check</li>
                            </ul>
                        </div>
                        <div style="background: #f7fafc; padding: 20px; border-radius: 8px;">
                            <h3>Quick Test:</h3>
                            <button class="btn btn-secondary" onclick="testAPI()">Test API Connection</button>
                            <div id="api-test-result" style="margin-top: 10px;"></div>
                        </div>
                    </div>
                    </div>

                    <!-- Databases Tab -->
                    <div id="databases" class="tab-pane">
                        <h2>💾 Databases</h2>
                        <p>Manage data using built-in tools. Mongo Express is proxied through the dashboard for secure in-cluster access.</p>
                        <div style="margin: 16px 0; display: flex; gap: 10px; flex-wrap: wrap;">
                            <a href="/proxy/mongo-express/" class="btn btn-primary" target="_blank">Open Mongo Express (new tab)</a>
                            <button class="btn btn-secondary" onclick="loadMongoExpress()">Open Inline</button>
                            <a href="http://mongodb-orchestrator-service:8000/docs" target="_blank" class="btn btn-secondary">Mongo Orchestrator Docs</a>
                        </div>
                        <iframe id="mongo-express-iframe" class="iframe-container" style="display:none;" src=""></iframe>
                    </div>

                    <!-- Service Apps (Discovered) Tab -->
                    <div id="apps" class="tab-pane">
                        <h2>📲 Service Apps</h2>
                        <p>Automatically discovered UIs from services with nexus.service.* labels.</p>
                        <div style="margin: 10px 0;">
                            <button class="btn btn-secondary" onclick="loadDiscoveredApps()">Refresh</button>
                        </div>
                        <div id="apps-container" class="service-grid">
                            <div class="loading">Discovering apps...</div>
                        </div>
                    </div>
                </div>
            
            <!-- Vertical Sidebar -->
            <div class="sidebar">
                <div class="sidebar-header">
                    <h3>Platform Tools</h3>
                    <p>Select a service to manage</p>
                </div>
                <div class="tabs-container" id="tabs-container">
                    <!-- Tabs will be generated dynamically -->
                </div>
            </div>
        </div>
        
        <script>
            // Tabs will be fetched from backend dynamically (data-driven)
            // Current user state derived from Keycloak
            let currentUserRole = 'platform-admin';
            let currentUserGroups = [];
            let keycloakConfig = null;
            let _kc = null;
            function loadScript(src) {
                return new Promise((resolve, reject) => {
                    const s = document.createElement('script');
                    s.src = src;
                    s.onload = resolve;
                    s.onerror = reject;
                    document.head.appendChild(s);
                });
            }
            function parseJwt (token) {
                try {
                    const base64Url = token.split('.')[1];
                    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                    }).join(''));
                    return JSON.parse(jsonPayload);
                } catch (e) { return {}; }
            }
            
            async function initializeTabs() {
                const container = document.getElementById('tabs-container');
                let html = '';
                try {
                    const token = _kc?.token || localStorage.getItem('access_token');
                    const resp = await fetch('/api/ui/tabs', {
                        headers: token ? { 'Authorization': 'Bearer ' + token } : {}
                    });
                    const data = await resp.json();
                    const tabs = Array.isArray(data?.tabs) ? data.tabs : [];
                    tabs.forEach(tab => {
                        const isDisabled = tab.enabled === false;
                        const click = isDisabled ? '' : (tab.type === 'external' && tab.url) ? `window.open('${tab.url}','_blank')` : `showTab('${tab.id}')`;
                        html += `
                            <button class="tab ${isDisabled ? 'disabled' : ''}" 
                                    onclick="${click}"
                                    title="${tab.description || ''}">
                                <div class="tab-icon">${tab.icon || '📁'}</div>
                                <div class="tab-content">
                                    <div class="tab-name">${tab.name}</div>
                                    <div class="tab-description">${tab.description || ''}</div>
                                </div>
                            </button>
                        `;
                    });
                } catch (e) {
                    console.error('Failed to load tabs', e);
                    html = '<div class="error">Failed to load tabs.</div>';
                }
                container.innerHTML = html;
            }
            
            function showTab(tabName) {
                // Hide all tab panes
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected tab pane
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked tab
                event.target.closest('.tab').classList.add('active');
                
                // Auto-load data based on tab
                if (tabName === 'loki') {
                    fetchLogs('{app="log-generator"}');
                } else if (tabName === 'grafana') {
                    loadMetricsOverview();
                } else if (tabName === 'prometheus') {
                    loadPrometheusOverview();
                } else if (tabName === 'databases') {
                    loadMongoExpress(true);
                } else if (tabName === 'apps') {
                    loadDiscoveredApps();
                } else if (tabName === 'apisix') {
                    loadApisix(true);
                } else if (tabName === 'kafka-ui') {
                    loadKafkaUI(true);
                }
            }
            
            async function loadServices() {
                const container = document.getElementById('services-container');
                container.innerHTML = '<div class="loading">Loading services...</div>';
                
                try {
                    const response = await fetch('/api/services');
                    const data = await response.json();
                    
                    let html = '';
                    let runningCount = 0;
                    let stoppedCount = 0;
                    
                    data.services.forEach(service => {
                        const isRunning = service.status === 'Running';
                        if (isRunning) runningCount++;
                        else stoppedCount++;
                        
                        html += `
                            <div class="service-card">
                                <div class="service-name">${service.name}</div>
                                <div class="service-namespace">Namespace: ${service.namespace}</div>
                                <div class="service-status ${isRunning ? 'status-running' : 'status-stopped'}">
                                    ${service.status} (${service.replicas} replicas)
                                </div>
                                <div class="service-actions">
                                    ${isRunning ? 
                                        `<button class="btn btn-danger" onclick="stopService('${service.name}')">Stop</button>` :
                                        `<button class="btn btn-success" onclick="startService('${service.name}')">Start</button>`
                                    }
                                    <button class="btn btn-secondary" onclick="refreshServices()">Refresh</button>
                                </div>
                            </div>
                        `;
                    });
                    
                    container.innerHTML = html;
                    
                    // Update stats with charts
                    updateStatsWithCharts(data.services.length, runningCount, stoppedCount);
                    
                } catch (error) {
                    container.innerHTML = '<div class="error">Error loading services: ' + error.message + '</div>';
                }
            }
            
            function updateStatsWithCharts(total, running, stopped) {
                // Update numbers
                document.getElementById('total-services').textContent = total;
                document.getElementById('running-services').textContent = running;
                document.getElementById('stopped-services').textContent = stopped;
                
                // Update charts
                const totalPercentage = total > 0 ? (total / 10) * 100 : 0;
                const runningPercentage = total > 0 ? (running / total) * 100 : 0;
                const stoppedPercentage = total > 0 ? (stopped / total) * 100 : 0;
                
                // Animate total services chart
                setTimeout(() => {
                    document.getElementById('total-chart').style.height = Math.min(totalPercentage, 80) + '%';
                }, 100);
                setTimeout(() => {
                    document.getElementById('total-chart2').style.height = Math.min(totalPercentage * 0.7, 60) + '%';
                }, 300);
                setTimeout(() => {
                    document.getElementById('total-chart3').style.height = Math.min(totalPercentage * 0.5, 40) + '%';
                }, 500);
                
                // Animate running services chart
                setTimeout(() => {
                    document.getElementById('running-chart').style.transform = `scaleX(${runningPercentage / 100})`;
                }, 200);
                
                // Animate stopped services chart
                setTimeout(() => {
                    document.getElementById('stopped-chart').style.height = Math.min(stoppedPercentage * 2, 70) + '%';
                }, 400);
            }
            
            async function stopService(name) {
                try {
                    const response = await fetch(`/api/services/${name}/stop`, { method: 'POST' });
                    if (response.ok) {
                        alert(`Service ${name} stopped successfully!`);
                        loadServices();
                    } else {
                        alert(`Error stopping service ${name}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function startService(name) {
                try {
                    const response = await fetch(`/api/services/${name}/start`, { method: 'POST' });
                    if (response.ok) {
                        alert(`Service ${name} started successfully!`);
                        loadServices();
                    } else {
                        alert(`Error starting service ${name}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function testAPI() {
                const resultDiv = document.getElementById('api-test-result');
                resultDiv.innerHTML = '<div class="loading">Testing API...</div>';
                
                try {
                    const response = await fetch('/api/services');
                    const data = await response.json();
                    resultDiv.innerHTML = `<div style="color: green;">✅ API is working! Found ${data.services.length} services.</div>`;
                } catch (error) {
                    resultDiv.innerHTML = `<div style="color: red;">❌ API Error: ${error.message}</div>`;
                }
            }
            
            function refreshServices() {
                loadServices();
            }
            
            // Embedded service loading functions

            function loadMongoExpress(inlineOnly=false) {
                const iframe = document.getElementById('mongo-express-iframe');
                if (!iframe) return;
                iframe.src = '/proxy/mongo-express/';
                iframe.style.display = 'block';
                if (!inlineOnly) {
                    window.open('/proxy/mongo-express/', '_blank');
                }
            }

            async function loadDiscoveredApps() {
                const container = document.getElementById('apps-container');
                if (!container) return;
                container.innerHTML = '<div class="loading">Discovering apps...</div>';
                try {
                    const resp = await fetch('/api/discovered-services');
                    const data = await resp.json();
                    if (!data.services || data.services.length === 0) {
                        container.innerHTML = '<div class="error">No discoverable services found. Ensure services have labels nexus.service.*</div>';
                        return;
                    }
                    let html = '';
                    data.services.forEach(svc => {
                        const title = (svc.icon ? svc.icon + ' ' : '') + svc.name;
                        html += `
                        <div class="service-card">
                            <div class="service-name">${title}</div>
                            <div class="service-namespace">Namespace: ${svc.namespace}</div>
                            <div style="margin:8px 0; font-size:12px; color:#718096;">Port: ${svc.port || '-'} ${svc.url ? `(url: ${svc.url})` : ''}</div>
                            <div class="service-actions">
                                <a class="btn btn-primary" href="/proxy/service/${svc.namespace}/${svc.name}${svc.port ? '/' + svc.port : ''}/" target="_blank">Open</a>
                            </div>
                        </div>`;
                    });
                    container.innerHTML = html;
                } catch (e) {
                    container.innerHTML = `<div class="error">Failed to load discovered apps: ${e.message}</div>`;
                }
            }

            
            async function loadMetricsOverview() {
                try {
                    // Get basic metrics from Prometheus API
                    const response = await fetch('/api/metrics-overview');
                    const data = await response.json();
                    
                    document.getElementById('cpu-usage').textContent = data.cpu_usage + '%';
                    document.getElementById('memory-usage').textContent = data.memory_usage + '%';
                    document.getElementById('pod-count').textContent = data.pod_count;
                    document.getElementById('service-count').textContent = data.service_count;
                    
                } catch (error) {
                    console.error('Error loading metrics:', error);
                    document.getElementById('cpu-usage').textContent = 'N/A';
                    document.getElementById('memory-usage').textContent = 'N/A';
                    document.getElementById('pod-count').textContent = 'N/A';
                    document.getElementById('service-count').textContent = 'N/A';
                }
            }
            
            function refreshGrafana() {
                const iframe = document.getElementById('grafana-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            
            function loadPrometheusEmbedded() {
                const iframe = document.getElementById('prometheus-iframe');
                const loading = document.getElementById('prometheus-loading');
                
                loading.style.display = 'block';
                iframe.style.display = 'none';
                
                iframe.onload = function() {
                    loading.style.display = 'none';
                    iframe.style.display = 'block';
                };
                
                iframe.onerror = function() {
                    loading.innerHTML = '<div class="error">Failed to load Prometheus. Please try opening in a new tab.</div>';
                };
                
                iframe.src = 'http://localhost:9090';
            }
            function loadApisix(inlineOnly=false) {
                const iframe = document.getElementById('apisix-iframe');
                if (!iframe) return;
                iframe.src = '/proxy/apisix/';
                iframe.style.display = 'block';
                if (!inlineOnly) { window.open('/proxy/apisix/', '_blank'); }
            }

            function loadKafkaUI(inlineOnly=false) {
                const iframe = document.getElementById('kafka-iframe');
                if (!iframe) return;
                iframe.src = '/proxy/kafka-ui/';
                iframe.style.display = 'block';
                if (!inlineOnly) { window.open('/proxy/kafka-ui/', '_blank'); }
            }
            
            function refreshPrometheus() {
                const iframe = document.getElementById('prometheus-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            

            
            async function fetchLogs(query) {
                const logStream = document.getElementById('log-stream');
                try {
                    const response = await fetch(`/api/logs?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.logs && data.logs.length > 0) {
                        let html = '';
                        data.logs.forEach(log => {
                            const timestamp = new Date(log.timestamp).toLocaleTimeString();
                            const level = log.level || 'INFO';
                            const color = level === 'ERROR' ? '#ff6b6b' : level === 'WARN' ? '#ffd93d' : '#6bcf7f';
                            html += `<div style="margin-bottom: 8px;"><span style="color: #888;">[${timestamp}]</span> <span style="color: ${color};">[${level}]</span> <span style="color: #fff;">${log.message}</span></div>`;
                        });
                        logStream.innerHTML = html;
                    } else {
                        logStream.innerHTML = '<div style="color: #888;">No logs found. Try a different query or check if services are generating logs.</div>';
                    }
                } catch (error) {
                    logStream.innerHTML = `<div style="color: #ff6b6b;">Error loading logs: ${error.message}</div>`;
                }
            }
            
            function queryLogs(query) {
                fetchLogs(query);
            }
            
            async function loadPrometheusOverview() {
                try {
                    const response = await fetch('/api/prometheus-overview');
                    const data = await response.json();
                    
                    document.getElementById('up-services').textContent = data.up_services;
                    document.getElementById('cpu-usage-prom').textContent = data.cpu_usage + '%';
                    document.getElementById('memory-usage-prom').textContent = data.memory_usage + '%';
                    document.getElementById('request-rate').textContent = data.request_rate + '/s';
                    
                } catch (error) {
                    console.error('Error loading Prometheus metrics:', error);
                    document.getElementById('up-services').textContent = 'N/A';
                    document.getElementById('cpu-usage-prom').textContent = 'N/A';
                    document.getElementById('memory-usage-prom').textContent = 'N/A';
                    document.getElementById('request-rate').textContent = 'N/A';
                }
            }
            
            async function queryPrometheus(query) {
                try {
                    const response = await fetch(`/api/prometheus-query?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    const resultDiv = document.getElementById('prometheus-query-result');
                    const contentDiv = document.getElementById('query-result-content');
                    
                    if (data.result && data.result.length > 0) {
                        let html = `<strong>Query: ${query}</strong><br><br>`;
                        data.result.forEach(item => {
                            html += `<div style="margin-bottom: 8px;">`;
                            html += `<strong>${item.metric.job || 'Unknown'}</strong>: ${item.value[1]}<br>`;
                            html += `<small style="color: #666;">Labels: ${JSON.stringify(item.metric)}</small>`;
                            html += `</div>`;
                        });
                        contentDiv.innerHTML = html;
                    } else {
                        contentDiv.innerHTML = `<strong>Query: ${query}</strong><br><br>No data found for this query.`;
                    }
                    
                    resultDiv.style.display = 'block';
                    
                } catch (error) {
                    const resultDiv = document.getElementById('prometheus-query-result');
                    const contentDiv = document.getElementById('query-result-content');
                    contentDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
                    resultDiv.style.display = 'block';
                }
            }
            
            function refreshLoki() {
                const iframe = document.getElementById('loki-iframe');
                if (iframe.style.display !== 'none') {
                    iframe.src = iframe.src;
                }
            }
            
            // User dropdown functions
            function toggleUserMenu() {
                const dropdown = document.getElementById('user-dropdown');
                dropdown.classList.toggle('show');
            }
            
            function showUserProfile() {
                alert('User Profile - Coming Soon!');
                // TODO: Implement user profile modal/page
                toggleUserMenu();
            }
            
            function showUserSettings() {
                alert('User Settings - Coming Soon!');
                // TODO: Implement user settings modal/page
                toggleUserMenu();
            }
            
            async function logout() {
                if (confirm('Are you sure you want to logout?')) {
                    try {
                        const token = localStorage.getItem('access_token');
                        if (token) {
                            // Call Auth API logout endpoint (best-effort)
                            await fetch('http://auth-api-service:8084/api/auth/logout', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                }
                            }).catch(()=>{});
                        }
                        // Clear server session cookie
                        try { await fetch('/session/logout', { method: 'POST' }); } catch (e) { /* no-op */ }
                    } catch (error) {
                        console.warn('Logout API call failed, but clearing local data:', error);
                    }

                    // Clear local storage and redirect to the landing page
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_info');
                    window.location.href = '/';
                }
            }
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(event) {
                const userProfile = document.querySelector('.user-profile');
                const dropdown = document.getElementById('user-dropdown');
                
                if (!userProfile.contains(event.target) && dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            });
            
            // Initialize auth and dashboard
            document.addEventListener('DOMContentLoaded', async function() {
                try {
                    keycloakConfig = await fetch('/api/auth/config').then(r=>r.json());

                    // If we already have an access token from the redirect callback, use it
                    const storedToken = localStorage.getItem('access_token');
                    if (storedToken) {
                        // best-effort server whoami to audit and validate token
                        try { await fetch('/api/auth/whoami', { headers: { 'Authorization': 'Bearer ' + storedToken }}); } catch (e) { /* no-op */ }
                        const id = parseJwt(storedToken);
                        currentUserGroups = id.groups || [];
                        const username = id.preferred_username || id.email || 'User';
                        document.getElementById('current-user').textContent = username;
                        document.getElementById('current-role').textContent = (currentUserGroups.join(', ') || 'user');

                        // Route based on groups: admin preferred if both
                        const isAdmin = currentUserGroups.includes(keycloakConfig.requiredAdminGroup);
                        const isCustomer = currentUserGroups.includes(keycloakConfig.requiredCustomerGroup);
                        if (isAdmin || isCustomer) {
                            const dest = isAdmin ? '/admin' : '/customer/';
                            const params = new URLSearchParams(window.location.search);
                            const tab = params.get('tab');
                            if (tab) { window.location.href = dest + '?tab=' + encodeURIComponent(tab); return; }
                            window.location.href = dest; return;
                        }

                        // If token present but no recognized groups, re-run login
                        window.location.href = '/start-login';
                        return;
                    }

                    // No token: start the Keycloak login flow
                    window.location.href = '/start-login';
                } catch (e) {
                    console.error('Auth init failed', e);
                    // fallback to explicit login start
                    window.location.href = '/start-login';
                }
            });
            
            async function loadUserInfo() {
                try {
                    // Try to get user info from Auth API
                    const token = localStorage.getItem('auth_token');
                    if (token) {
                        const response = await fetch(`http://localhost:8084/api/auth/user-info?token=${token}`);
                        if (response.ok) {
                            const userData = await response.json();
                            document.getElementById('current-user').textContent = userData.name || userData.username || 'Platform Admin';
                            document.getElementById('current-role').textContent = userData.role || 'platform-admin';
                        }
                    }
                } catch (error) {
                    console.log('Could not load user info from Auth API:', error);
                    // Keep default values
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/start-login")
async def start_login(request: Request):
    """Redirect to Keycloak for admin client using normalized origin (works behind proxies)."""
    origin = _normalized_origin(request)
    redirect_uri = origin + '/auth/callback'
    client_id = ADMIN_CLIENT_ID
    auth_url = f"{KEYCLOAK_PUBLIC_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth?client_id={quote_plus(client_id)}&redirect_uri={quote_plus(redirect_uri)}&response_type=token&scope=openid%20profile%20email"
    return RedirectResponse(url=auth_url)


@app.get("/start-signup")
async def start_signup(request: Request):
    """Redirect user to Keycloak self-registration for this client using the same callback (normalized origin)."""
    origin = _normalized_origin(request)
    redirect_uri = origin + '/auth/callback'
    client_id = ADMIN_CLIENT_ID
    reg_url = (
        f"{KEYCLOAK_PUBLIC_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/registrations"
        f"?client_id={quote_plus(client_id)}&redirect_uri={quote_plus(redirect_uri)}&response_type=token&scope=openid%20profile%20email"
    )
    return RedirectResponse(url=reg_url)


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback():
        """A tiny client-side callback page to capture the access token from the fragment (#) and store it in localStorage.
        Then it calls /api/auth/whoami (best-effort) and redirects to /admin or /customer based on groups.
        """
        # Inject required group names into the client script so routing decisions are consistent with server config
        admin_group = REQUIRED_ADMIN_GROUP
        customer_group = REQUIRED_CUSTOMER_GROUP
        page = f"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Auth Callback</title>
        </head>
        <body>
            <script>
                (function(){{
                    try {{
                        var hash = window.location.hash.substring(1);
                        var params = new URLSearchParams(hash);
                        var access_token = params.get('access_token');
                        if (!access_token) {{
                            document.body.innerText = 'No access token found in callback.';
                            return;
                        }}
                        // persist token for app usage
                        localStorage.setItem('access_token', access_token);
                        // establish server session (HttpOnly cookie)
                        fetch('/session/login', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ access_token: access_token }})
                        }}).catch(function(){{ /* best-effort */ }});
                        // whoami to let server audit and to retrieve groups
                        fetch('/api/auth/whoami', {{ headers: {{ 'Authorization': 'Bearer ' + access_token }} }}).then(function(r){{
                            return r.json();
                        }}).then(function(data){{
                            var groups = (data && data.groups) || [];
                            var adminGroup = "{admin_group}";
                            var customerGroup = "{customer_group}";
                            if (groups.indexOf(adminGroup) !== -1) {{
                                window.location.href = '/admin';
                            }} else if (groups.indexOf(customerGroup) !== -1) {{
                                window.location.href = '/customer/';
                            }} else {{
                                // default destination when groups are missing: admin
                                window.location.href = '/admin';
                            }}
                        }}).catch(function(e){{
                            console.error('whoami failed', e);
                            window.location.href = '/admin';
                        }});
                    }} catch (e) {{
                        console.error(e);
                        document.body.innerText = 'Auth callback error';
                    }}
                }})();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=page)

@app.post("/session/login")
async def session_login(request: Request):
    """Set an HttpOnly cookie with the access token for server-side route protection."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    token = str((data or {}).get("access_token") or "")
    if not token:
        raise HTTPException(status_code=400, detail="access_token required")
    # Verify token (no group requirement here; route handlers will enforce as needed)
    await verify_jwt_token(token)
    resp = JSONResponse({"ok": True})
    # For dev, secure=False. Consider True when served over HTTPS.
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False)
    return resp

@app.post("/session/logout")
async def session_logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    return resp


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    html = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Nexus - The Center of Connections</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <script>
        tailwind.config = { theme: { extend: { colors: { 'nexus-blue': '#1a73e8', 'nexus-dark': '#1e293b', 'nexus-light': '#f1f5f9' }, fontFamily: { sans: ['Inter','sans-serif'] } } } };
    </script>
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap\" rel=\"stylesheet\">
    <style>
        .tile-shadow { transition: all 0.3s ease; box-shadow: 0 10px 15px -3px rgba(0,0,0,.05), 0 4px 6px -2px rgba(0,0,0,.05); }
        .tile-shadow:hover { box-shadow: 0 20px 25px -5px rgba(26,115,232,.2), 0 10px 10px -5px rgba(26,115,232,.1); transform: translateY(-5px); }
        .collapsed { max-height: 0; padding-top: 0 !important; padding-bottom: 0 !important; opacity: 0; transition: max-height .5s ease-out, padding .5s ease-out, opacity .3s ease-out; overflow: hidden; }
    </style>
    <script>
      function startLogin(){ window.location.href = '/start-login'; }
      function startSignup(){ window.location.href = '/start-signup'; }
    </script>
</head>
<body class=\"font-sans bg-nexus-light text-nexus-dark\">
    <header class=\"sticky top-0 z-50 bg-white shadow-lg\">
        <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
            <div class=\"flex justify-between items-center h-16\">
                <div class=\"flex-shrink-0\">
                    <span class=\"text-3xl font-extrabold text-nexus-blue tracking-tight\">Nexus</span>
                    <span class=\"hidden sm:inline text-xs ml-2 text-gray-500 italic\">The center of connections.</span>
                </div>
                <div class=\"flex items-center space-x-4\">
                    <nav class=\"hidden md:flex space-x-8\">
                        <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Home</a>
                        <a href=\"#services\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Services</a>
                        <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">About Us</a>
                        <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Contact</a>
                    </nav>
                    <button id=\"hero-toggle\" class=\"hidden sm:inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full text-gray-700 bg-gray-100 hover:bg-gray-200\">Hide Hero</button>
                    <div class=\"flex items-center space-x-2\">
                      <button onclick=\"startSignup()\" class=\"px-4 py-2 bg-white text-nexus-blue border border-nexus-blue text-sm font-semibold rounded-full hover:bg-nexus-light transition shadow-sm\">Sign up</button>
                      <button onclick=\"startLogin()\" class=\"px-4 py-2 bg-nexus-blue text-white text-sm font-semibold rounded-full hover:bg-nexus-blue/90 transition shadow-md\">Sign in</button>
                    </div>
                    <button class=\"md:hidden text-gray-600 hover:text-nexus-blue\">
                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"w-6 h-6\"><line x1=\"3\" y1=\"12\" x2=\"21\" y2=\"12\"></line><line x1=\"3\" y1=\"6\" x2=\"21\" y2=\"6\"></line><line x1=\"3\" y1=\"18\" x2=\"21\" y2=\"18\"></line></svg>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <main>
        <section id=\"hero-section\" class=\"relative pt-16 pb-24 lg:pt-24 lg:pb-32 bg-white overflow-hidden shadow-inner\">
            <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center\">
                <div class=\"lg:w-3/4 mx-auto\">
                    <h1 class=\"text-5xl sm:text-6xl lg:text-7xl font-extrabold text-nexus-dark leading-tight mb-4\">IT Solutions at <span class=\"text-nexus-blue\">The Center of Connections.</span></h1>
                    <p class=\"text-xl sm:text-2xl text-gray-500 mb-8 max-w-3xl mx-auto\">Nexus delivers integrated, future-proof IT services designed to keep your business running seamlessly and securely, connecting you to tomorrow's possibilities.</p>
                    <div class=\"flex justify-center space-x-4\">
                        <a href=\"#services\" class=\"px-8 py-3 text-lg font-bold text-white bg-nexus-blue rounded-full shadow-xl hover:bg-nexus-blue/90\">Explore Our Services</a>
                        <a href=\"#\" class=\"px-8 py-3 text-lg font-bold text-nexus-dark bg-white border-2 border-nexus-blue rounded-full shadow-xl hover:bg-nexus-light\">Get a Quote</a>
                    </div>
                </div>
            </div>
        </section>

        <section id=\"services\" class=\"py-20 lg:py-32\">
            <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
                <h2 class=\"text-4xl font-bold text-center mb-4 text-nexus-dark\">Our Core IT Services</h2>
                <p class=\"text-lg text-gray-500 text-center mb-16\">Choose from our suite of products and services designed for reliability, speed, and security.</p>
                <div id=\"services-container\" class=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8\"></div>
            </div>
        </section>

        <section class=\"bg-nexus-blue py-16\">
            <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center\">
                <h2 class=\"text-3xl sm:text-4xl font-extrabold text-white mb-4\">Ready to Build Your Future?</h2>
                <p class=\"text-lg text-nexus-light mb-8 max-w-2xl mx-auto\">Let Nexus be the bridge between your current capabilities and your next major technological leap.</p>
                <a href=\"#\" class=\"px-10 py-4 text-xl font-bold text-nexus-blue bg-white rounded-full shadow-2xl hover:bg-gray-100\">Start Your Project Now</a>
            </div>
        </section>
    </main>

    <footer class=\"bg-nexus-dark text-white py-8\">
        <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center text-center md:text-left\">
            <div class=\"mb-4 md:mb-0\">
                <span class=\"text-2xl font-extrabold text-nexus-blue\">Nexus</span>
                <p class=\"text-sm text-gray-400 mt-1\">&copy; 2025 Nexus. All rights reserved.</p>
            </div>
            <div class=\"flex space-x-6 text-sm\">
                <a href=\"#\" class=\"hover:text-nexus-blue\">Privacy Policy</a>
                <a href=\"#\" class=\"hover:text-nexus-blue\">Terms of Service</a>
                <a href=\"#\" class=\"hover:text-nexus-blue\">Careers</a>
            </div>
        </div>
    </footer>

    <script>
        const heroSection = document.getElementById('hero-section');
        const heroToggleButton = document.getElementById('hero-toggle');
        function toggleHero(){ if(heroSection.classList.contains('collapsed')){ heroSection.classList.remove('collapsed'); heroToggleButton.textContent='Hide Hero'; } else { heroSection.classList.add('collapsed'); heroToggleButton.textContent='Show Hero'; } }
        if(heroToggleButton){ heroToggleButton.addEventListener('click', toggleHero); }

        function createServiceTile(service){
            const color = service.color || '#1a73e8';
            const iconInner = service.icon || '';
            const title = service.title || service.id;
            const desc = service.description || '';
            const infoUrl = service.infoPageUrl || '#';
            const serviceUrl = service.servicePageUrl || '#';
            return `
                <div class=\"bg-white p-8 rounded-xl tile-shadow border-t-4\" style=\"border-top-color: ${color};\">
                    <div class=\"flex items-center mb-4\">
                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"36\" height=\"36\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"${color}\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"mr-3\">${iconInner}</svg>
                        <h3 class=\"text-2xl font-semibold text-nexus-dark\">${title}</h3>
                    </div>
                    <p class=\"text-gray-600 mb-6\">${desc}</p>
                    <div class=\"flex space-x-4\">
                        <a href=\"${infoUrl}\" class=\"text-sm font-semibold text-nexus-blue hover:underline\">Info Page &rarr;</a>
                        <span class=\"text-gray-300\">|</span>
                        <a href=\"${serviceUrl}\" class=\"text-sm font-semibold text-nexus-blue hover:underline\">Service Page &rarr;</a>
                    </div>
                </div>`;
        }

        async function renderServices(){
            const container = document.getElementById('services-container');
            if(!container) return;
            container.innerHTML = '<div class="col-span-full text-center text-gray-500">Loading...</div>';
            try{
                const resp = await fetch('/api/ui/public');
                const data = await resp.json();
                const tabs = Array.isArray(data && data.tabs) ? data.tabs : [];
                if(!tabs.length){
                    container.innerHTML = '<div class="col-span-full text-center text-red-500">No services configured. Add docs to MongoDB collection ui_tabs with show_on_landing=true.</div>';
                    return;
                }
                container.innerHTML = tabs.map(createServiceTile).join('');
            } catch(e){
                container.innerHTML = '<div class="col-span-full text-center text-red-500">Failed to load services: ' + (e && e.message || e) + '</div>';
            }
        }

        window.onload = renderServices;
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

@app.get("/api/services")
def get_services(_: Dict[str, Any] = Depends(ensure_admin)) -> Dict[str, Any]:
    start_time = time.time()
    try:
        deployments = v1.list_deployment_for_all_namespaces(watch=False)
        services: list[Dict[str, Any]] = []
        running_count = 0
        total_count = 0
        
        for dep in deployments.items:
            total_count += 1
            is_running = dep.status.replicas == dep.spec.replicas and dep.spec.replicas > 0
            if is_running:
                running_count += 1
                
            services.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "status": "Running" if is_running else "Stopped"
            })
        
        # Update metrics
        total_services.set(total_count)
        active_services.set(running_count)
        
        return {"services": services}
    except Exception as e:
        http_requests_total.labels(method='GET', endpoint='/api/services', status='500').inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(method='GET', endpoint='/api/services').observe(duration)
        http_requests_total.labels(method='GET', endpoint='/api/services', status='200').inc()

@app.post("/api/services/{name}/stop")
def stop_service(name: str, request: Request, _: Dict[str, Any] = Depends(ensure_admin)):
    try:
        body = {"spec": {"replicas": 0}}
        v1.patch_namespaced_deployment(name=name, namespace="default", body=body)
        return {"status": f"Service {name} stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/services/{name}/start")
def start_service(name: str, request: Request, _: Dict[str, Any] = Depends(ensure_admin)):
    try:
        body = {"spec": {"replicas": 1}} # Assumes 1 replica, can be more dynamic
        v1.patch_namespaced_deployment(name=name, namespace="default", body=body)
        return {"status": f"Service {name} started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/auth/config")
async def auth_config():
    """Frontend will fetch this to init keycloak-js"""
    return {
        "url": KEYCLOAK_PUBLIC_URL,
        "realm": KEYCLOAK_REALM,
        "adminClientId": ADMIN_CLIENT_ID,
        "customerClientId": CUSTOMER_CLIENT_ID,
        "requiredAdminGroup": REQUIRED_ADMIN_GROUP,
        "requiredCustomerGroup": REQUIRED_CUSTOMER_GROUP,
    }

@app.get("/api/auth/whoami")
async def whoami(request: Request):
    """Return caller identity (from JWT) and write an audit record when configured."""
    payload = await verify_jwt(request)
    await _audit_event(payload, event_type="whoami", request=request)
    return {
        "user": {
            "sub": payload.get("sub"),
            "preferred_username": payload.get("preferred_username"),
            "email": payload.get("email"),
        },
        "groups": payload.get("groups", []),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "iss": payload.get("iss"),
        "aud": payload.get("aud"),
    }

@app.get("/login")
async def login_page():
    """Login page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Platform - Login</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                width: 100%;
                max-width: 400px;
            }
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            .login-header h1 {
                color: #333;
                margin: 0;
                font-size: 24px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                box-sizing: border-box;
            }
            .login-btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .login-btn:hover {
                transform: translateY(-2px);
            }
            .error-message {
                color: #e74c3c;
                text-align: center;
                margin-top: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>🔐 Nexus Platform</h1>
                <p>Sign in to access the admin dashboard</p>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Sign In</button>
            </form>
            <div id="errorMessage" class="error-message"></div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorMessage = document.getElementById('errorMessage');
                
                try {
                    const response = await fetch('http://auth-api-service:8084/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('refresh_token', data.refresh_token);
                        localStorage.setItem('user_info', JSON.stringify(data.user));
                        
                        // Redirect to dashboard
                        window.location.href = '/admin';
                    } else {
                        const errorData = await response.json();
                        errorMessage.textContent = errorData.message || 'Login failed';
                        errorMessage.style.display = 'block';
                    }
                } catch (error) {
                    errorMessage.textContent = 'Network error. Please try again.';
                    errorMessage.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/logs")
async def get_logs(query: str = "{app=\"log-generator\"}") -> Dict[str, Any]:
    """Fetch logs from Kubernetes pods using Python client"""
    try:
        from kubernetes import client, config  # type: ignore
        
        # Load in-cluster config
        try:
            config.load_incluster_config()  # type: ignore
        except Exception:
            # Fallback to default config for local development
            config.load_kube_config()  # type: ignore

        v1 = client.CoreV1Api()  # type: ignore

        # Get logs from log-generator pods
        logs: list[Dict[str, str]] = []
        try:
            # Get pods with label app=log-generator
            pods = v1.list_namespaced_pod(  # type: ignore
                namespace="default",
                label_selector="app=log-generator"
            )

            for pod in pods.items:
                if pod.status.phase == 'Running':
                    # Get logs from the pod
                    pod_logs = v1.read_namespaced_pod_log(  # type: ignore
                        name=pod.metadata.name,
                        namespace="default",
                        tail_lines=50,
                        timestamps=True
                    )

                    # Parse logs
                    for line in pod_logs.strip().split('\n'):
                        if line.strip():
                            # Parse timestamp and message
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                timestamp_str = parts[0]
                                message = parts[1]

                                # Extract log level
                                level = 'INFO'
                                if '[ERROR]' in message:
                                    level = 'ERROR'
                                elif '[WARN]' in message:
                                    level = 'WARN'

                                logs.append({
                                    'timestamp': timestamp_str,
                                    'level': level,
                                    'message': message
                                })

                    break  # Only get logs from first running pod

            return {"logs": logs[-20:]}  # Return last 20 logs

        except Exception as e:
            return {"logs": [], "error": f"Failed to fetch logs: {str(e)}"}

    except Exception as e:
        return {"logs": [], "error": str(e)}

@app.get("/api/metrics-overview")
async def get_metrics_overview() -> Dict[str, Any]:
    """Get basic metrics overview for embedded display"""
    try:
        # Get basic cluster metrics
        import subprocess
        
        # Get pod count
        result = subprocess.run([
            'kubectl', 'get', 'pods', '--all-namespaces', '--field-selector=status.phase=Running', '-o', 'json'
        ], capture_output=True, text=True, timeout=10)
        
        pod_count: int = 0
        if result.returncode == 0:
            import json
            pods_data = json.loads(result.stdout)
            pod_count = len(pods_data.get('items', []))
        
        # Get service count
        result = subprocess.run([
            'kubectl', 'get', 'services', '--all-namespaces', '-o', 'json'
        ], capture_output=True, text=True, timeout=10)
        
        service_count: int = 0
        if result.returncode == 0:
            services_data = json.loads(result.stdout)
            service_count = len(services_data.get('items', []))
        
        # Get real CPU and memory usage from Prometheus
        try:
            import requests
            base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
            
            # Get CPU usage
            cpu_response = requests.get(f"{base_url}/api/v1/query", params={"query": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"}, timeout=5)
            cpu_data = cpu_response.json()
            cpu_usage = 0
            if cpu_data.get('data', {}).get('result'):
                cpu_usage = round(float(cpu_data['data']['result'][0]['value'][1]), 1)
            
            # Get memory usage
            mem_response = requests.get(f"{base_url}/api/v1/query", params={"query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"}, timeout=5)
            mem_data = mem_response.json()
            memory_usage = 0
            if mem_data.get('data', {}).get('result'):
                memory_usage = round(float(mem_data['data']['result'][0]['value'][1]), 1)
                
        except Exception as e:
            # Fallback to simulated values if Prometheus is not available
            import random
            cpu_usage = random.randint(15, 45)  # 15-45%
            memory_usage = random.randint(30, 70)  # 30-70%
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "pod_count": pod_count,
            "service_count": service_count
        }
        
    except Exception as e:
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "pod_count": 0,
            "service_count": 0,
            "error": str(e)
        }

@app.get("/api/prometheus-overview")
async def get_prometheus_overview():
    """Get basic Prometheus metrics overview"""
    try:
        import requests
        
        # Query Prometheus API
        base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
        
        # Get services up count
        up_response = requests.get(f"{base_url}/api/v1/query", params={"query": "up"}, timeout=5)
        up_data = up_response.json()
        up_services = len(up_data.get('data', {}).get('result', []))
        
        # Get CPU usage
        cpu_response = requests.get(f"{base_url}/api/v1/query", params={"query": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"}, timeout=5)
        cpu_data = cpu_response.json()
        cpu_usage = 0
        if cpu_data.get('data', {}).get('result'):
            cpu_usage = round(float(cpu_data['data']['result'][0]['value'][1]), 1)
        
        # Get memory usage
        mem_response = requests.get(f"{base_url}/api/v1/query", params={"query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"}, timeout=5)
        mem_data = mem_response.json()
        memory_usage = 0
        if mem_data.get('data', {}).get('result'):
            memory_usage = round(float(mem_data['data']['result'][0]['value'][1]), 1)
        
        # Get request rate
        req_response = requests.get(f"{base_url}/api/v1/query", params={"query": "rate(http_requests_total[5m])"}, timeout=5)
        req_data = req_response.json()
        request_rate = 0
        if req_data.get('data', {}).get('result'):
            request_rate = round(float(req_data['data']['result'][0]['value'][1]), 2)
        
        return {
            "up_services": up_services,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "request_rate": request_rate
        }
        
    except Exception as e:
        return {
            "up_services": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "request_rate": 0,
            "error": str(e)
        }

@app.get("/api/prometheus-query")
async def query_prometheus(query: str):
    """Execute a Prometheus query"""
    try:
        import requests
        
        base_url = "http://nexus-observability-kube-p-prometheus.monitoring.svc.cluster.local:9090"
        response = requests.get(f"{base_url}/api/v1/query", params={"query": query}, timeout=10)
        
        return response.json()
        
    except Exception as e:
        return {"error": str(e)}
# Tue Aug 12 16:28:47 MST 2025

@app.get("/api/discovered-services")
def discovered_services(_: Dict[str, Any] = Depends(ensure_admin)):
    """Discover services that expose UIs via labels and return minimal info.
    Looks for Services with labels nexus.service.* and returns name, namespace, port, and optional icon/url.
    """
    try:
        core = client.CoreV1Api()
        svcs = core.list_service_for_all_namespaces(watch=False)
        out = []
        for s in svcs.items:
            labels = (s.metadata.labels or {})
            if any(k.startswith("nexus.service.") for k in labels.keys()):
                # pick first port if not labeled
                port = labels.get("nexus.service.port")
                if not port and s.spec.ports:
                    port = str(s.spec.ports[0].port)
                out.append({
                    "name": s.metadata.name,
                    "namespace": s.metadata.namespace,
                    "port": port,
                    "icon": labels.get("nexus.service.icon"),
                    "url": labels.get("nexus.service.url"),
                })
        return {"services": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _proxy_request(target_base: str, path: str, request: Request):
    """Helper to proxy incoming request to target_base/path, preserving method, headers, and body where reasonable."""
    url = target_base.rstrip('/') + '/' + path.lstrip('/')
    method = request.method
    headers = dict(request.headers)
    # Remove hop-by-hop headers
    for h in ["host", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"]:
        headers.pop(h, None)
    async with httpx.AsyncClient(timeout=30.0) as client_http:
        body = await request.body()
        resp = await client_http.request(method, url, headers=headers, content=body, params=dict(request.query_params))
    # Stream back response
    excluded = set(["content-encoding", "transfer-encoding", "connection"])
    resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
    return StreamingResponse(iter([resp.content]), status_code=resp.status_code, headers=dict(resp_headers), media_type=resp.headers.get("content-type"))


def _rewrite_location_for_keycloak(location: str) -> str:
    """Rewrite upstream Keycloak Location header to our proxied base '/keycloak'.
    Examples:
      http://keycloak-service:8080/realms/nexus/... -> /keycloak/realms/nexus/...
      /realms/nexus/... -> /keycloak/realms/nexus/...
      already under /keycloak -> unchanged
    """
    try:
        if not location:
            return location
        if location.startswith('/keycloak'):
            return location
        # Absolute URL from internal service
        if location.startswith(KEYCLOAK_INTERNAL_URL):
            suffix = location[len(KEYCLOAK_INTERNAL_URL):]
            if not suffix.startswith('/'):
                suffix = '/' + suffix
            return '/keycloak' + suffix
        # Absolute but different host: leave as-is
        # Relative root path
        if location.startswith('/'):
            return '/keycloak' + location
        return location
    except Exception:
        return location


@app.api_route('/keycloak', methods=["GET"])  # convenience to add trailing slash
async def keycloak_root_redirect():
    return JSONResponse({"message": "Keycloak proxy root. Use /keycloak/ for console."})


@app.api_route('/keycloak/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_keycloak(request: Request, path: str = ""):
    """Public reverse proxy to Keycloak so browsers can hit '/keycloak/...'."""
    # Build upstream URL
    target_base = KEYCLOAK_INTERNAL_URL
    url = target_base.rstrip('/') + '/' + path.lstrip('/')
    method = request.method
    headers = dict(request.headers)
    for h in ["host", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"]:
        headers.pop(h, None)
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client_http:
        body = await request.body()
        resp = await client_http.request(method, url, headers=headers, content=body, params=dict(request.query_params))
    # Copy headers and rewrite Location if present
    excluded = set(["content-encoding", "transfer-encoding", "connection"])
    hdrs = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}
    if 'location' in {k.lower() for k in hdrs.keys()}:
        # normalize access preserving original casing may be complex; set explicitly
        loc_val = None
        for k in list(hdrs.keys()):
            if k.lower() == 'location':
                loc_val = hdrs.pop(k)
                break
        if loc_val is not None:
            hdrs['Location'] = _rewrite_location_for_keycloak(loc_val)
    return StreamingResponse(iter([resp.content]), status_code=resp.status_code, headers=hdrs, media_type=resp.headers.get("content-type"))


@app.api_route('/proxy/mongo-express/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_mongo_express(request: Request, path: str = "", _: Dict[str, Any] = Depends(ensure_admin)):
    target = "http://mongo-express.default.svc.cluster.local:8081"
    return await _proxy_request(target, path, request)


@app.api_route('/proxy/apisix/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_apisix(request: Request, path: str = "", _: Dict[str, Any] = Depends(ensure_admin)):
    target = APISIX_DASHBOARD_URL
    return await _proxy_request(target, path, request)


@app.api_route('/proxy/kafka-ui/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_kafka_ui(request: Request, path: str = "", _: Dict[str, Any] = Depends(ensure_admin)):
    target = KAFKA_UI_URL
    return await _proxy_request(target, path, request)


@app.api_route('/proxy/service/{namespace}/{name}/{port}/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_service_with_port(request: Request, namespace: str, name: str, port: str, path: str = "", _: Dict[str, Any] = Depends(ensure_admin)):
    target = f"http://{name}.{namespace}.svc.cluster.local:{port}"
    return await _proxy_request(target, path, request)


@app.api_route('/proxy/service/{namespace}/{name}/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_service(request: Request, namespace: str, name: str, path: str = "", _: Dict[str, Any] = Depends(ensure_admin)):
    # Discover service to get its first port
    core = client.CoreV1Api()
    svc = core.read_namespaced_service(name=name, namespace=namespace)
    port = svc.spec.ports[0].port
    target = f"http://{name}.{namespace}.svc.cluster.local:{port}"
    return await _proxy_request(target, path, request)

@app.api_route('/customer/{path:path}', methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_customer_portal(request: Request, path: str = "", _: Dict[str, Any] = Depends(ensure_customer)):
    """Single-entry: proxy to the Customer Portal under the admin dashboard host."""
    target = "http://customer-portal.default.svc.cluster.local:8002"
    return await _proxy_request(target, path, request)
