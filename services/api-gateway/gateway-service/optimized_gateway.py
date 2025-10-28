#!/usr/bin/env python3
"""Optimized API Gateway for Nexus Platform.
Provides:
  * External service proxy (landing-page, auth)
  * Internal service delegation (/api/*)
  * Health endpoint (/health)
Now resilient when landing-page service is unavailable (returns fallback page instead of 502).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import typing, os, logging, json, ipaddress, requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FALLBACK_LANDING_HTML = b"""<!DOCTYPE html><html><head><title>Nexus Landing (Degraded)</title><style>body{font-family:Arial;margin:40px;background:#111;color:#eee} .box{background:#222;padding:20px;border-radius:8px;max-width:640px} a{color:#82aaff}</style></head><body><div class='box'><h1>Nexus Platform</h1><p>Landing page service is currently unavailable.</p><ul><li><a href='/health'>Gateway Health</a></li><li><a href='/api/'>API Root</a> (if exposed)</li></ul><p>Status: <strong>DEGRADED</strong></p></div></body></html>"""

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")

IN_CLUSTER = env_bool("RUN_IN_CLUSTER", True)  # assume True when running in k8s

class OptimizedGatewayHandler(BaseHTTPRequestHandler):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        # External service config (host/port adjustable via env)
        landing_host = os.getenv("LANDING_PAGE_HOST", "landing-page-service" if IN_CLUSTER else "localhost")
        landing_port = int(os.getenv("LANDING_PAGE_PORT", "8000"))
        auth_host = os.getenv("AUTH_SERVICE_HOST", "auth" if IN_CLUSTER else "localhost")
        auth_port = int(os.getenv("AUTH_SERVICE_PORT", "8080"))

        self.external_services: dict[str, dict[str, typing.Any]] = {
            'landing-page': {
                'host': landing_host,
                'port': landing_port,
                'base_path': '/'
            },
            'auth': {
                'host': auth_host,
                'port': auth_port,
                'base_path': '/realms/nexus-platform'
            }
        }

        # Internal service discovery (use service DNS names in cluster)
        self.internal_services: dict[str, str] = {
            'access-control': os.getenv('ACCESS_CONTROL_ADDR', 'access-control-service:8000' if IN_CLUSTER else 'localhost:8083'),
            'auth-api': os.getenv('AUTH_API_ADDR', 'auth-api-service:8084' if IN_CLUSTER else 'localhost:8084'),
            'admin-dashboard': os.getenv('ADMIN_DASHBOARD_ADDR', 'admin-dashboard-service:8000' if IN_CLUSTER else 'localhost:8081')
        }

        self.allowed_ips = [
            ipaddress.ip_network('127.0.0.0/8'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16')
        ]
        self.executor = ThreadPoolExecutor(max_workers=10)
        super().__init__(*args, **kwargs)

    # --------------- Core HTTP Methods ---------------
    def do_GET(self):  # noqa: N802
        try:
            if not self.is_ip_allowed():
                return self.safe_send_error(403, "Access denied")
            parsed = urlparse(self.path)
            self.route_request(parsed.path, parse_qs(parsed.query))
        except BrokenPipeError:
            logger.warning("Client disconnected during GET")
        except Exception as e:  # noqa: BLE001
            logger.exception("Unhandled GET error: %s", e)
            self.safe_send_error(500, "Internal server error")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    # --------------- Helpers ---------------
    def is_ip_allowed(self) -> bool:
        client_ip = ipaddress.ip_address(self.client_address[0])
        return any(client_ip in net for net in self.allowed_ips)

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    # --------------- Routing ---------------
    def route_request(self, path: str, query: dict[str, list[str]]):
        logger.info("Routing %s from %s", path, self.client_address[0])
        if path == '/health':
            return self.get_health()
        if path in ['/', '/index.html']:
            return self.proxy_to_external_service('landing-page', '/', query, allow_fallback=True)
        if path.startswith('/landing'):
            return self.proxy_to_external_service('landing-page', path, query, allow_fallback=True)
        if path.startswith('/auth/') or path.startswith('/realms/'):
            return self.proxy_to_external_service('auth', path, query)
        if path.startswith('/api/'):
            return self.delegate_to_service_mesh(path, query)
        self.safe_send_error(404, "Not found")

    # --------------- Proxy Logic ---------------
    def proxy_to_external_service(self, service_name: str, path: str, query: dict[str, list[str]], allow_fallback: bool = False):
        try:
            svc = self.external_services[service_name]
            q = '&'.join([f"{k}={v[0]}" for k, v in query.items()])
            target = f"http://{svc['host']}:{svc['port']}{path}"
            if q:
                target += f"?{q}"
            logger.info("Proxy -> %s : %s", service_name, target)
            resp = requests.get(target, timeout=5)
            self.send_response(resp.status_code)
            for h, v in resp.headers.items():
                if h.lower() not in ['transfer-encoding', 'connection']:
                    self.send_header(h, v)
            self.send_cors_headers()
            self.end_headers()
            try:
                self.wfile.write(resp.content)
            except BrokenPipeError:
                logger.warning("Client disconnected while writing body")
        except requests.exceptions.RequestException as e:  # network error
            logger.error("Proxy error (%s): %s", service_name, e)
            if allow_fallback and service_name == 'landing-page':
                self._serve_fallback_landing()
            else:
                self.safe_send_error(502, f"External service {service_name} unavailable")

    def _serve_fallback_landing(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        try:
            self.wfile.write(FALLBACK_LANDING_HTML)
        except BrokenPipeError:
            logger.warning("Client disconnected before fallback page sent")

    # --------------- Internal Delegation ---------------
    def delegate_to_service_mesh(self, path: str, query: dict[str, list[str]]):
        try:
            parts = path.split('/')
            if len(parts) < 3:
                return self.safe_send_error(400, "Invalid API path")
            category = parts[2]
            if category == 'auth':
                service_name = 'auth-api'
            elif category == 'services':
                service_name = 'access-control'
            else:
                service_name = 'access-control'
            addr = self.internal_services.get(service_name)
            if not addr:
                return self.safe_send_error(503, f"Service {service_name} not registered")
            q = '&'.join([f"{k}={v[0]}" for k, v in query.items()])
            target = f"http://{addr}{path}" + (f"?{q}" if q else '')
            logger.info("Mesh delegate -> %s : %s", service_name, target)
            resp = requests.get(target, timeout=3)
            self.send_response(resp.status_code)
            for h, v in resp.headers.items():
                if h.lower() not in ['transfer-encoding', 'connection']:
                    self.send_header(h, v)
            self.send_cors_headers()
            self.end_headers()
            try:
                self.wfile.write(resp.content)
            except BrokenPipeError:
                logger.warning("Client disconnected during mesh write")
        except requests.exceptions.RequestException as e:
            logger.error("Mesh delegation error: %s", e)
            self.safe_send_error(502, "Service mesh unavailable")

    # --------------- Health ---------------
    def get_health(self):
        payload = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'gateway': 'optimized',
            'in_cluster': IN_CLUSTER,
            'external_services': {k: {'host': v['host'], 'port': v['port']} for k, v in self.external_services.items()},
        }
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        try:
            self.wfile.write(json.dumps(payload).encode())
        except BrokenPipeError:
            logger.warning("Client disconnected during health write")

    # --------------- Error & Logging ---------------
    def safe_send_error(self, code: int, message: str):
        try:
            self.send_error(code, message)
        except BrokenPipeError:
            logger.warning("Client disconnected while sending error %s", code)

    def log_message(self, format: str, *args: typing.Any) -> None:  # noqa: A003
        logger.info("%s - %s", self.client_address[0], format % args)


def run_optimized_gateway():
    try:
        port = int(os.getenv('GATEWAY_PORT', '8080'))
        httpd = HTTPServer(('', port), OptimizedGatewayHandler)
        logger.info("🚀 Optimized API Gateway running on port %s", port)
        logger.info("📊 Health    : http://localhost:%s/health", port)
        logger.info("🔗 Landing   : http://localhost:%s/", port)
        logger.info("🔐 Auth      : http://localhost:%s/auth/*", port)
        logger.info("🕸️  Internal : http://localhost:%s/api/*", port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Gateway stopped by user")
    except Exception as e:  # noqa: BLE001
        logger.exception("Gateway fatal error: %s", e)


if __name__ == '__main__':
    run_optimized_gateway()
