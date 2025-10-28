import os
from typing import Optional, Dict, Any, cast
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import httpx
from jose import jwt, JWTError
from cachetools import TTLCache
from urllib.parse import urljoin, urlencode

# Config
# Browser-facing Keycloak base (keep as '/keycloak' so we can proxy through this service locally)
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_URL", "/keycloak")
# Internal Keycloak service for server-to-server calls (discovery/JWKS)
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak-service:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "nexus")
ADMIN_CLIENT_ID = os.getenv("ADMIN_CLIENT_ID", "admin-dashboard")
CUSTOMER_CLIENT_ID = os.getenv("CUSTOMER_CLIENT_ID", "customer-portal")
LANDING_CLIENT_ID = os.getenv("LANDING_CLIENT_ID", "nexus-landing")
REQUIRED_ADMIN_GROUP = os.getenv("REQUIRED_ADMIN_GROUP", "platform-admins")
REQUIRED_CUSTOMER_GROUP = os.getenv("REQUIRED_CUSTOMER_GROUP", "customers")
ADMIN_BASE_URL = os.getenv("ADMIN_BASE_URL", "")
CUSTOMER_BASE_URL = os.getenv("CUSTOMER_BASE_URL", "")
# Upstream internal services for proxying
ADMIN_INTERNAL_URL = os.getenv("ADMIN_INTERNAL_URL", "http://admin-dashboard-service:8000")
CUSTOMER_INTERNAL_URL = os.getenv("CUSTOMER_INTERNAL_URL", "http://customer-portal:8002")
# Admin service public tabs API (landing will proxy /api/ui/public -> this URL)
MONGODB_UI_API = os.getenv("UI_TABS_API", "/api/ui/public")

# Use internal URL for discovery/JWKS
OIDC_DISCOVERY = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
jwks_uri: Optional[str] = None
_issuer_discovered: Optional[str] = None
_jwks_cache: TTLCache[str, Any] = TTLCache(maxsize=1, ttl=300)

app = FastAPI(title="Nexus Landing")

def _normalized_origin(request: Request) -> str:
    # Prefer forwarded headers (Codespaces/Proxies) then fall back
    xf_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    xf_host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()
    scheme = xf_proto or (request.url.scheme or "http")
    host = xf_host or request.headers.get("host") or "localhost"
    # Always strip default ports so they match Keycloak redirect URI entries
    if host.endswith(":443"):
        host = host[:-4]
    if host.endswith(":80"):
        host = host[:-3]
    return f"{scheme}://{host}"

async def _get_jwks() -> Dict[str, Any]:
    global jwks_uri, _issuer_discovered
    if "jwks" in _jwks_cache:
        return _jwks_cache["jwks"]
    async with httpx.AsyncClient(timeout=10.0) as c:
        if jwks_uri is None:
            r = await c.get(OIDC_DISCOVERY)
            r.raise_for_status()
            data = r.json()
            jwks_uri = data.get("jwks_uri")
            _issuer_discovered = data.get("issuer")
        if not jwks_uri:
            raise RuntimeError("Could not determine JWKS URI from OIDC discovery")
        r2 = await c.get(jwks_uri)
        r2.raise_for_status()
        jwks = r2.json()
        _jwks_cache["jwks"] = jwks
        return jwks

@app.get("/start-login")
async def start_login(request: Request):
    origin = _normalized_origin(request)
    redirect_uri = origin + '/auth/callback'
    params = {
        "client_id": LANDING_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "token",
        "scope": "openid profile email",
    }
    query = urlencode(params, safe=":/", doseq=True)
    auth_url = f"{KEYCLOAK_PUBLIC_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth?{query}"
    return RedirectResponse(url=auth_url)

@app.get("/start-signup")
async def start_signup(request: Request):
    origin = _normalized_origin(request)
    redirect_uri = origin + '/auth/callback'
    params = {
        "client_id": LANDING_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "token",
        "scope": "openid profile email",
    }
    query = urlencode(params, safe=":/", doseq=True)
    reg_url = f"{KEYCLOAK_PUBLIC_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/registrations?{query}"
    return RedirectResponse(url=reg_url)

@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback():
    admin_group = REQUIRED_ADMIN_GROUP
    customer_group = REQUIRED_CUSTOMER_GROUP
    # Prefer proxying via current host. Allow override via env if explicitly set.
    admin_base = ADMIN_BASE_URL.rstrip('/') if ADMIN_BASE_URL else ''
    customer_base = CUSTOMER_BASE_URL.rstrip('/') if CUSTOMER_BASE_URL else ''
    page = f"""
        <!doctype html><html><head><meta charset='utf-8'><title>Auth Callback</title></head><body>
            <script>
                (function(){{
                    try {{
                        var hash = window.location.hash.substring(1);
                        var params = new URLSearchParams(hash);
                        var access_token = params.get('access_token');
                        if (!access_token) {{ document.body.innerText='No access token found'; return; }}
                        localStorage.setItem('access_token', access_token);
                        // establish server session (HttpOnly cookie) for cross-portal access
                        fetch('/session/login', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ access_token: access_token }}) }}).catch(function(){{}});

                        var preferred = localStorage.getItem('preferredPortal');
                        var adminBase = "{admin_base}" || '';
                        var customerBase = "{customer_base}" || '';

                        // Support group name variants (e.g., platform-admin vs platform-admins)
                        var ADMIN_SYNONYMS = (function(){{
                            var set = new Set();
                            var base = "{admin_group}".toLowerCase();
                            set.add(base);
                            if (base.endsWith('s')) set.add(base.slice(0,-1));
                            set.add('platform-admin'); set.add('platform-admins');
                            set.add('admin'); set.add('admins');
                            return Array.from(set);
                        }})();
                        var CUSTOMER_SYNONYMS = (function(){{
                            var set = new Set();
                            var base = "{customer_group}".toLowerCase();
                            set.add(base);
                            if (base.endsWith('s')) set.add(base.slice(0,-1));
                            set.add('customer'); set.add('customers');
                            return Array.from(set);
                        }})();

                        function routeByGroups(data) {{
                            var groups = ((data && data.groups) || []).map(function(g){{ return String(g).toLowerCase(); }});
                            var isAdmin = groups.some(function(g){{ return ADMIN_SYNONYMS.indexOf(g) !== -1; }});
                            var isCustomer = groups.some(function(g){{ return CUSTOMER_SYNONYMS.indexOf(g) !== -1; }});

                            if (isAdmin && isCustomer) {{
                                if (preferred === 'admin') {{ window.location.href = adminBase + '/admin'; return; }}
                                if (preferred === 'customer') {{ window.location.href = customerBase + '/customer/'; return; }}
                                // Render a banner with choices
                                document.body.innerHTML = `
                                    <div style="font-family: sans-serif; display:flex; align-items:center; justify-content:center; min-height: 100vh; background:#f8fafc;">
                                        <div style="background:#fff; padding:24px; border-radius:12px; box-shadow:0 10px 20px rgba(0,0,0,0.08); max-width:560px; text-align:center;">
                                            <h2 style="margin:0 0 8px; font-size:24px;">Choose your portal</h2>
                                            <p style="margin:0 0 16px; color:#475569;">Your account has access to both Admin Dashboard and Customer Portal.</p>
                                            <div style="display:flex; gap:12px; justify-content:center; margin:12px 0 16px;">
                                                <button id="go-admin" style="padding:10px 16px; background:#2563eb; color:#fff; border:none; border-radius:8px; cursor:pointer;">Go to Admin Dashboard</button>
                                                <button id="go-customer" style="padding:10px 16px; background:#10b981; color:#fff; border:none; border-radius:8px; cursor:pointer;">Go to Customer Portal</button>
                                            </div>
                                            <label style="font-size:14px; color:#334155; display:inline-flex; align-items:center; gap:8px;">
                                                <input id="remember" type="checkbox" /> Remember my choice
                                            </label>
                                        </div>
                                    </div>`;
                                var remember = document.getElementById('remember');
                                document.getElementById('go-admin').onclick = function(){{ if (remember.checked) localStorage.setItem('preferredPortal','admin'); window.location.href=adminBase + '/admin'; }};
                                document.getElementById('go-customer').onclick = function(){{ if (remember.checked) localStorage.setItem('preferredPortal','customer'); window.location.href=customerBase + '/customer/'; }};
                                return;
                            }}

                            if (isAdmin) {{ window.location.href=adminBase + '/admin'; return; }}
                            if (isCustomer) {{ window.location.href=customerBase + '/customer/'; return; }}
                            window.location.href=adminBase + '/admin';
                        }}

                        // Attempt immediately, then retry once after a short delay to accommodate profile updates
                        fetch('/api/auth/whoami', {{ headers: {{ 'Authorization': 'Bearer ' + access_token }} }})
                            .then(function(r){{ return r.json(); }}).then(routeByGroups)
                            .catch(function(){{ setTimeout(function(){{
                                fetch('/api/auth/whoami', {{ headers: {{ 'Authorization': 'Bearer ' + access_token }} }})
                                    .then(function(r){{ return r.json(); }}).then(routeByGroups)
                                    .catch(function(){{ window.location.href = adminBase + '/admin'; }});
                            }}, 500); }});
                    }} catch(e) {{ console.error(e); document.body.innerText='Callback error'; }}
                }})();
            </script>
        </body></html>
        """
    return HTMLResponse(page)

@app.post("/session/login")
async def session_login(request: Request):
    try:
        incoming = await request.json()
        if isinstance(incoming, dict):
            data: Dict[str, Any] = cast(Dict[str, Any], incoming)
        else:
            data = {}
    except Exception:
        data = {}
    token = str((data or {}).get("access_token") or "")
    if not token:
        raise HTTPException(status_code=400, detail="access_token required")
    # Verify token minimally to avoid setting junk
    jwks = await _get_jwks()
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="No matching JWKS key")
        options = {"verify_aud": False}
        alg = key.get("alg", "RS256")
        issuer = _issuer_discovered
        try:
            if issuer:
                jwt.decode(token, key, algorithms=[alg], options=options, issuer=issuer)
            else:
                options["verify_iss"] = False
                jwt.decode(token, key, algorithms=[alg], options=options)
        except JWTError:
            # Fallback: ignore issuer mismatches (proxy/public vs internal issuer)
            options["verify_iss"] = False
            jwt.decode(token, key, algorithms=[alg], options=options)
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    resp = JSONResponse({"ok": True})
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False)
    return resp

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    # Enhanced Tailwind landing to more closely match the provided mock
    html = """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
            <title>Nexus – The Center of Connections</title>
            <script src=\"https://cdn.tailwindcss.com\"></script>
            <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap\" rel=\"stylesheet\" />
            <script>
                tailwind.config = { theme: { extend: { colors: { nexus: { blue:'#2563eb', dark:'#0f172a', light:'#f1f5f9' } }, fontFamily: { sans:['Inter','ui-sans-serif','system-ui'] } } } };
                function startLogin(){ window.location.href='/start-login'; }
                function startSignup(){ window.location.href='/start-signup'; }
            </script>
            <style>
                .tile-shadow { transition: all .25s ease; box-shadow: 0 10px 15px -3px rgba(0,0,0,.05),0 4px 6px -2px rgba(0,0,0,.05); }
                .tile-shadow:hover { transform: translateY(-4px); box-shadow: 0 25px 35px -10px rgba(37,99,235,.25), 0 10px 15px -5px rgba(37,99,235,.15); }
                .gradient-bg { background: radial-gradient(1000px 500px at 50% -10%, rgba(37,99,235,.20), rgba(37,99,235,0) 60%), linear-gradient(180deg,#ffffff 0%, #f8fafc 100%); }
            </style>
        </head>
        <body class=\"font-sans bg-nexus-light text-slate-800\">
            <!-- Header -->
            <header class=\"sticky top-0 z-50 bg-white/90 backdrop-blur shadow-sm\">
                <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
                    <div class=\"h-16 flex items-center justify-between\">
                        <div class=\"flex items-center gap-2\">
                            <div class=\"w-8 h-8 rounded-lg bg-nexus-blue/10 grid place-items-center\"><span class=\"text-nexus-blue text-lg font-black\">N</span></div>
                            <span class=\"text-2xl sm:text-3xl font-extrabold text-nexus-blue tracking-tight\">Nexus</span>
                            <span class=\"hidden md:inline text-xs ml-2 text-gray-500 italic\">The center of connections.</span>
                        </div>
                        <nav class=\"hidden md:flex items-center gap-8 text-sm\">
                            <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Home</a>
                            <a href=\"#services\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Services</a>
                            <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">About</a>
                            <a href=\"#\" class=\"text-gray-600 hover:text-nexus-blue font-medium\">Contact</a>
                        </nav>
                        <div class=\"flex items-center gap-2\">
                            <button onclick=\"startSignup()\" class=\"px-4 py-2 bg-white text-nexus-blue border border-nexus-blue text-sm font-semibold rounded-full hover:bg-nexus-light transition shadow-sm\">Sign up</button>
                            <button onclick=\"startLogin()\" class=\"px-4 py-2 bg-nexus-blue text-white text-sm font-semibold rounded-full hover:bg-nexus-blue/90 transition shadow-sm\">Sign in</button>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Hero -->
            <section class=\"gradient-bg\">
                <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24 text-center\">
                    <h1 class=\"text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight\">IT Solutions at <span class=\"text-nexus-blue\">The Center of Connections.</span></h1>
                    <p class=\"mt-5 text-lg sm:text-xl text-slate-500 max-w-3xl mx-auto\">Nexus delivers integrated, future-proof IT services designed to keep your business running seamlessly and securely, connecting you to tomorrow's possibilities.</p>
                    <div class=\"mt-8 flex items-center justify-center gap-4\">
                        <a href=\"#services\" class=\"px-6 sm:px-8 py-3 text-base sm:text-lg font-bold text-white bg-nexus-blue rounded-full shadow-lg hover:bg-nexus-blue/90\">Explore Our Services</a>
                        <a href=\"#\" class=\"px-6 sm:px-8 py-3 text-base sm:text-lg font-bold text-slate-700 bg-white border-2 border-nexus-blue rounded-full shadow hover:bg-slate-50\">Get a Quote</a>
                    </div>
                </div>
            </section>

            <!-- Services -->
            <section id=\"services\" class=\"py-16 lg:py-24\">
                <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
                    <h2 class=\"text-3xl lg:text-4xl font-bold text-center text-slate-900\">Our Core IT Services</h2>
                    <p class=\"mt-3 text-lg text-slate-500 text-center\">Choose from our suite of products and services designed for reliability, speed, and security.</p>
                    <div id=\"services-container\" class=\"mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8\"></div>
                </div>
            </section>

            <!-- CTA Strip -->
            <section class=\"bg-nexus-blue\">
                <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 text-center\">
                    <h3 class=\"text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white\">Ready to Build Your Future?</h3>
                    <p class=\"mt-3 text-lg text-nexus-light max-w-2xl mx-auto\">Let Nexus be the bridge between your current capabilities and your next major technological leap.</p>
                    <a href=\"#\" class=\"mt-6 inline-block px-8 py-3 text-lg font-bold text-nexus-blue bg-white rounded-full shadow-2xl hover:bg-gray-100\">Start Your Project Now</a>
                </div>
            </section>

            <!-- Footer -->
            <footer class=\"bg-slate-950 text-white\">
                <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row items-center justify-between gap-4\">
                    <div class=\"flex items-center gap-2\">
                        <span class=\"text-2xl font-extrabold text-nexus-blue\">Nexus</span>
                        <span class=\"text-sm text-slate-400\">© 2025 Nexus</span>
                    </div>
                    <div class=\"flex items-center gap-6 text-sm text-slate-300\">
                        <a href=\"#\" class=\"hover:text-nexus-blue\">Privacy</a>
                        <a href=\"#\" class=\"hover:text-nexus-blue\">Terms</a>
                        <a href=\"#\" class=\"hover:text-nexus-blue\">Careers</a>
                    </div>
                </div>
            </footer>

            <script>
                function createServiceTile(service){
                    const color = service.color || '#2563eb';
                    const iconInner = service.icon || '';
                    const title = service.title || service.id || 'Service';
                    const desc = service.description || '';
                    const infoUrl = service.infoPageUrl || '#';
                    const serviceUrl = service.servicePageUrl || '#';
                    return `
                        <article class=\"bg-white p-8 rounded-xl border border-slate-200 tile-shadow\" style=\"border-top-width:4px; border-top-color:${color};\">
                            <div class=\"flex items-center mb-4\">
                                <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"36\" height=\"36\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"${color}\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"mr-3\">${iconInner}</svg>
                                <h3 class=\"text-2xl font-semibold text-slate-900\">${title}</h3>
                            </div>
                            <p class=\"text-slate-600 mb-6\">${desc}</p>
                            <div class=\"flex flex-wrap items-center gap-4\">
                                <a href=\"${infoUrl}\" class=\"text-sm font-semibold text-nexus-blue hover:underline\">Info Page →</a>
                                <span class=\"text-slate-300\">|</span>
                                <a href=\"${serviceUrl}\" class=\"text-sm font-semibold text-nexus-blue hover:underline\">Service Page →</a>
                            </div>
                        </article>`;
                }

                async function renderServices(){
                    const container = document.getElementById('services-container');
                    if(!container) return;
                    container.innerHTML = '<div class="col-span-full text-center text-slate-500">Loading...</div>';
                    try {
                        const resp = await fetch('/api/ui/public');
                        const data = await resp.json();
                        const tabs = Array.isArray(data && data.tabs) ? data.tabs : [];
                        if(!tabs.length){
                            container.innerHTML = '<div class="col-span-full text-center text-red-500">No services configured.</div>';
                            return;
                        }
                        container.innerHTML = tabs.map(createServiceTile).join('');
                    } catch(e){
                        container.innerHTML = '<div class="col-span-full text-center text-red-500">Failed to load services</div>';
                    }
                }
                window.onload = renderServices;
            </script>
        </body>
        </html>
        """
    return HTMLResponse(html)

@app.get("/api/auth/whoami")
async def whoami_proxy(request: Request):
    # For now, just decode the token using discovered JWKS for routing purposes
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
        options = {"verify_aud": False}
        alg = key.get("alg", "RS256")
        issuer = _issuer_discovered
        try:
            if issuer:
                payload = jwt.decode(token, key, algorithms=[alg], options=options, issuer=issuer)
            else:
                options["verify_iss"] = False
                payload = jwt.decode(token, key, algorithms=[alg], options=options)
        except JWTError:
            options["verify_iss"] = False
            payload = jwt.decode(token, key, algorithms=[alg], options=options)
        return {"groups": payload.get("groups", [])}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.get("/api/ui/public")
async def public_tabs_proxy():
    # Proxy to configured UI_TABS_API so the landing at 18081 can fetch tiles.
    target = MONGODB_UI_API
    async with httpx.AsyncClient(timeout=10.0) as c:
        try:
            r = await c.get(target)
            r.raise_for_status()
            return JSONResponse(r.json())
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"UI tabs fetch failed: {e}")

# --- Reverse proxies ---
def _filter_headers(headers: Dict[str, str]) -> Dict[str, str]:
    # Drop headers that shouldn't be forwarded or set by client
    hop_by_hop = {
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade', 'host', 'content-length', 'accept-encoding'
    }
    return {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}

async def _proxy(request: Request, base_url: str, upstream_path: str):
    url = urljoin(base_url.rstrip('/') + '/', upstream_path.lstrip('/'))
    method = request.method
    headers = _filter_headers(dict(request.headers))
    # Forward cookies for session-based auth
    cookie_hdr = request.headers.get('cookie')
    if cookie_hdr:
        headers['cookie'] = cookie_hdr
    params = dict(request.query_params)
    data = await request.body()
    async with httpx.AsyncClient(follow_redirects=False, timeout=30.0) as client:
        r = await client.request(method, url, headers=headers, params=params, content=data)
    # Rewrite Location header if it points to internal Keycloak URL -> public proxy path
    response_headers = {k: v for k, v in r.headers.items() if k.lower() not in {'content-length', 'transfer-encoding', 'content-encoding', 'connection'}}
    loc = response_headers.get('Location') or response_headers.get('location')
    if loc and loc.startswith(KEYCLOAK_INTERNAL_URL):
        # replace internal with public proxy base
        public = KEYCLOAK_PUBLIC_URL.rstrip('/') + '/' + loc.replace(KEYCLOAK_INTERNAL_URL, '').lstrip('/')
        response_headers['Location'] = public
    return HTMLResponse(content=r.content, status_code=r.status_code, headers=response_headers)

@app.api_route("/keycloak", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def keycloak_root(request: Request):
    return await _proxy(request, KEYCLOAK_INTERNAL_URL, "/")

@app.api_route("/keycloak/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def keycloak_proxy(path: str, request: Request):
    return await _proxy(request, KEYCLOAK_INTERNAL_URL, path)

# Keycloak login pages often reference absolute root paths such as /realms/* and /resources/*.
# Mirror those to the Keycloak internal service so assets and form posts work through the landing host.
@app.api_route("/realms/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def keycloak_realms_proxy(path: str, request: Request):
    return await _proxy(request, KEYCLOAK_INTERNAL_URL, f"/realms/{path}")

@app.api_route("/resources/{path:path}", methods=["GET", "HEAD", "OPTIONS"])
async def keycloak_resources_proxy(path: str, request: Request):
    return await _proxy(request, KEYCLOAK_INTERNAL_URL, f"/resources/{path}")

# Back-compat for older Keycloak paths (not typically used in v24+ but harmless to include)
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def keycloak_auth_compat_proxy(path: str, request: Request):
    return await _proxy(request, KEYCLOAK_INTERNAL_URL, f"/auth/{path}")

@app.api_route("/admin", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def admin_root(request: Request):
    # Forward to upstream '/admin' so app renders under the same path.
    return await _proxy(request, ADMIN_INTERNAL_URL, "/admin")

@app.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def admin_proxy(path: str, request: Request):
    # Special-case auth initiators to upstream root paths
    if path in {"start-login", "start-signup"}:
        return await _proxy(request, ADMIN_INTERNAL_URL, f"/{path}")
    return await _proxy(request, ADMIN_INTERNAL_URL, f"/admin/{path}")

# Proxy admin service root-level APIs to ensure admin UI works behind landing host
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def admin_api_proxy(path: str, request: Request):
    # Avoid hijacking landing's own APIs
    if path in {"ui/public"} or path.startswith("auth/"):
        raise HTTPException(status_code=404, detail="Not found")
    return await _proxy(request, ADMIN_INTERNAL_URL, f"/api/{path}")

@app.api_route("/session/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def admin_session_proxy(path: str, request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, f"/session/{path}")

@app.api_route("/docs", methods=["GET", "HEAD"])
async def admin_docs_root(request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, "/docs")

@app.api_route("/docs/{path:path}", methods=["GET", "HEAD"])
async def admin_docs_proxy(path: str, request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, f"/docs/{path}")

@app.api_route("/openapi.json", methods=["GET", "HEAD"])
async def admin_openapi_proxy(request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, "/openapi.json")

@app.api_route("/metrics", methods=["GET", "HEAD"])
async def admin_metrics_proxy(request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, "/metrics")

@app.api_route("/health", methods=["GET", "HEAD"])
async def admin_health_proxy(request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, "/health")

@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def admin_misc_proxy(path: str, request: Request):
    return await _proxy(request, ADMIN_INTERNAL_URL, f"/proxy/{path}")

@app.api_route("/customer", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def customer_root(request: Request):
    return await _proxy(request, CUSTOMER_INTERNAL_URL, "/")

@app.api_route("/customer/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def customer_proxy(path: str, request: Request):
    return await _proxy(request, CUSTOMER_INTERNAL_URL, path)
