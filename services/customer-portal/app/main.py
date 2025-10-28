import os
from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
from jose import jwt, JWTError
from cachetools import TTLCache

if TYPE_CHECKING:
    # help type checkers with generic types
    from cachetools import TTLCache as _TTLCache


app = FastAPI(title="Customer Portal")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "nexus")
CLIENT_ID = os.getenv("CUSTOMER_CLIENT_ID", "customer-portal")
REQUIRED_GROUP = os.getenv("REQUIRED_CUSTOMER_GROUP", "customers")
OIDC_DISCOVERY = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
jwks_uri: Optional[str] = None
_jwks_cache: TTLCache[str, Any] = TTLCache(maxsize=1, ttl=300)

async def _get_jwks() -> Dict[str, Any]:
    global jwks_uri
    if "jwks" in _jwks_cache:
        return _jwks_cache["jwks"]
    async with httpx.AsyncClient(timeout=10.0) as c:
        if jwks_uri is None:
            r = await c.get(OIDC_DISCOVERY)
            r.raise_for_status()
            jwks_uri = r.json().get("jwks_uri")
        if not jwks_uri:
            raise RuntimeError("Could not determine JWKS URI from OIDC discovery")
        r2 = await c.get(jwks_uri)
        r2.raise_for_status()
        jwks = r2.json()
        _jwks_cache["jwks"] = jwks
        return jwks

async def verify_jwt(request: Request) -> Dict[str, Any]:
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
        issuer = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
        payload = jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], options={"verify_aud": False}, issuer=issuer)
        groups = payload.get("groups", [])
        if REQUIRED_GROUP not in groups:
            raise HTTPException(status_code=403, detail="Requires customers group")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def index(request: Request):
                # Require login: if no access_token in localStorage, redirect via simple JS to /start-login
                html = """
                <!doctype html>
                <html><head><meta charset='utf-8'><title>Customer Portal</title></head>
                <body style="font-family: sans-serif; padding: 24px;">
                        <h1>🛍️ Customer Portal</h1>
                        <div id="status">Checking session...</div>
                        <div id="app" style="display:none;">
                            <p>Welcome to the customer portal.</p>
                            <button onclick="fetch('/private',{headers:{'Authorization':'Bearer '+localStorage.getItem('access_token')}}).then(r=>r.json()).then(j=>alert(JSON.stringify(j))).catch(e=>alert(e))">Test /private</button>
                            <button onclick="localStorage.removeItem('access_token'); window.location='/start-login'">Logout</button>
                        </div>
                        <script>
                            (function(){
                                var t = localStorage.getItem('access_token');
                                if (!t) { window.location = '/start-login'; return; }
                                document.getElementById('status').textContent = 'Logged in';
                                document.getElementById('app').style.display='block';
                            })();
                        </script>
                </body></html>
                """
                return HTMLResponse(html)

@app.get("/api/auth/config")
async def auth_config():
        return {"url": KEYCLOAK_URL, "realm": KEYCLOAK_REALM, "clientId": CLIENT_ID, "requiredGroup": REQUIRED_GROUP}

@app.get("/start-login")
async def start_login(request: Request):
        host = request.headers.get('host') or 'localhost'
        origin = f"{request.url.scheme}://{host}" if request.url.scheme else f"http://{host}"
        redirect_uri = origin + '/auth/callback'
        auth_url = f"{KEYCLOAK_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&response_type=token&scope=openid%20profile%20email"
        return RedirectResponse(url=auth_url)

@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback():
        page = f"""
        <!doctype html><html><head><meta charset='utf-8'><title>Customer Auth</title></head><body>
        <script>
            (function(){{
                try {{
                    var hash = window.location.hash.substring(1);
                    var params = new URLSearchParams(hash);
                    var access_token = params.get('access_token');
                    if (!access_token) {{ document.body.innerText='No access token found'; return; }}
                    localStorage.setItem('access_token', access_token);
                    // Optionally validate group client-side, but server will check too
                    window.location.href = '/';
                }} catch(e) {{ console.error(e); document.body.innerText='Callback error'; }}
            }})();
        </script>
        </body></html>
        """
        return HTMLResponse(page)

@app.get("/private")
async def private_area(request: Request):
    await verify_jwt(request)
    return {"message": "You are in a protected area", "group": REQUIRED_GROUP}

@app.get("/api/auth/whoami")
async def whoami(request: Request):
    payload = await verify_jwt(request)
    return {
        "user": {
            "sub": payload.get("sub"),
            "preferred_username": payload.get("preferred_username"),
            "email": payload.get("email"),
        },
        "groups": payload.get("groups", []),
    }
