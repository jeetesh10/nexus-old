#!/usr/bin/env python3
"""Minimal development landing server with proxying.

Routes supported:
- /keycloak/* -> proxies to KEYCLOAK_PROXY_TARGET (default http://127.0.0.1:11000)
- /proxy/* -> proxies to API_PROXY_TARGET (default http://127.0.0.1:8083)
- /admin/* -> ADMIN_PROXY_TARGET (default http://127.0.0.1:8081)
- /customer/* -> CUSTOMER_PROXY_TARGET (default http://127.0.0.1:8084)
- /health -> 200 JSON

Serves static files from the directory where this script lives.
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import urllib.request
import urllib.error
import urllib.parse
import sys


class LandingHandler(SimpleHTTPRequestHandler):
    def _proxy(self, target_url, method='GET', body=None, rewrite_origin=None, rewrite_prefix=None, client_origin=None):
        # Build upstream request headers, forwarding essential ones
        headers = {}
        # Authorization (if any)
        auth = self.headers.get('Authorization')
        if auth:
            headers['Authorization'] = auth
        # Cookies are critical for Keycloak login flows
        cookie = self.headers.get('Cookie')
        if cookie:
            headers['Cookie'] = cookie
        # Preserve content-type for form posts/json
        ctype = self.headers.get('Content-Type')
        if ctype:
            headers['Content-Type'] = ctype
        # A few benign pass-throughs
        for h in ('Accept', 'Accept-Language', 'User-Agent', 'Origin', 'Referer'):
            v = self.headers.get(h)
            if v:
                headers[h] = v
        # Forward Host header for upstream and X-Forwarded-* to aid upstream context
        try:
            parsed_target = urllib.parse.urlparse(target_url)
            if parsed_target.netloc:
                headers['Host'] = parsed_target.netloc
        except Exception:
            pass
        # X-Forwarded-For chain
        xff = self.headers.get('X-Forwarded-For')
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else None
        if client_ip:
            headers['X-Forwarded-For'] = f"{xff}, {client_ip}" if xff else client_ip
        # Do not forward X-Forwarded-Proto/Host to avoid upstream rewriting links to client origin
        # (explicitly remove if present)
        if 'X-Forwarded-Proto' in headers:
            del headers['X-Forwarded-Proto']
        if 'X-Forwarded-Host' in headers:
            del headers['X-Forwarded-Host']
        data = None
        if body is not None:
            data = body if isinstance(body, (bytes, bytearray)) else body.encode('utf-8')
        req = urllib.request.Request(target_url, data=data, headers=headers, method=method)
        try:
                            if isinstance(data_bytes, (bytes, bytearray)) and ('text/html' in content_type or 'javascript' in content_type or 'text/css' in content_type):
                self.send_response(resp.getcode())
                # Collect headers into a dict (handle multi-value headers like Set-Cookie)
                headers_to_send = []
                for k, v in resp.getheaders():
                                        text = text.replace(rewrite_origin + '/', '/')
                    if kl in ('content-type', 'cache-control', 'set-cookie', 'location', 'www-authenticate', 'vary'):
                        # Rewrite Location header if pointing at Keycloak origin
                        if kl == 'location' and rewrite_prefix:
                            if rewrite_origin and v.startswith(rewrite_origin):
                                v = rewrite_prefix + v[len(rewrite_origin):]
                            # Do not rewrite root-absolute /realms or /resources to preserve cookie path alignment
                            # Also rewrite if Location points to current client origin + /realms|/resources
                                        text = text.replace(client_origin + '/', '/')
                                # Strip client origin so it becomes root-absolute (no /keycloak prefix)
                                #!/usr/bin/env python3
                                """Minimal development landing server with proxying.

                                Routes:
                                - /keycloak/* and root /realms/*, /resources/* -> Keycloak
                                - /proxy/* -> API proxy
                                - /admin/* and /customer/* -> respective backends
                                - /health -> simple JSON
                                """
                                from http.server import HTTPServer, SimpleHTTPRequestHandler
                                import os
                                import sys
                                import urllib.request
                                import urllib.error
                                import urllib.parse


                                class LandingHandler(SimpleHTTPRequestHandler):
                                    def _proxy(self, target_url, method='GET', body=None, strip_origins=None):
                                        if strip_origins is None:
                                            strip_origins = []

                                        # Build upstream headers
                                        headers = {}
                                        for h in ('Authorization', 'Cookie', 'Content-Type', 'Accept', 'Accept-Language', 'User-Agent', 'Origin', 'Referer'):
                                            v = self.headers.get(h)
                                            if v:
                                                headers[h] = v

                                        # X-Forwarded-For
                                        xff = self.headers.get('X-Forwarded-For')
                                        client_ip = self.client_address[0] if hasattr(self, 'client_address') else None
                                        if client_ip:
                                            headers['X-Forwarded-For'] = f"{xff}, {client_ip}" if xff else client_ip

                                        data = None
                                        if body is not None:
                                            data = body if isinstance(body, (bytes, bytearray)) else body.encode('utf-8')

                                        req = urllib.request.Request(target_url, data=data, headers=headers, method=method)
                                        try:
                                            with urllib.request.urlopen(req, timeout=20) as resp:
                                                status = resp.getcode()
                                                content_type = resp.headers.get('Content-Type', '')
                                                body_bytes = resp.read()

                                                # Rewrite Location absolute origins -> root-absolute
                                                self.send_response(status)
                                                for k, v in resp.getheaders():
                                                    if k.lower() == 'location' and v:
                                                        for origin in strip_origins:
                                                            if v.startswith(origin):
                                                                v = v[len(origin):]
                                                    if k.lower() == 'transfer-encoding':
                                                        continue
                                                    self.send_header(k, v)

                                                # Optionally rewrite absolute origins in HTML/CSS/JS to root '/'
                                                if ('text/html' in content_type) or ('text/css' in content_type) or ('javascript' in content_type):
                                                    try:
                                                        text = body_bytes.decode('utf-8', errors='ignore')
                                                        for origin in strip_origins:
                                                            text = text.replace(origin + '/', '/')
                                                        body_bytes = text.encode('utf-8')
                                                    except Exception:
                                                        pass

                                                self.send_header('Content-Length', str(len(body_bytes) if body_bytes else 0))
                                                self.end_headers()
                                                try:
                                                    self.wfile.write(body_bytes)
                                                except BrokenPipeError:
                                                    return
                                        except urllib.error.HTTPError as e:
                                            self.send_response(e.code)
                                            self.send_header('Content-Type', e.headers.get('Content-Type', 'text/plain'))
                                            self.end_headers()
                                            try:
                                                self.wfile.write(e.read())
                                            except Exception:
                                                pass
                                        except Exception as e:
                                            self.send_response(502)
                                            self.send_header('Content-Type', 'text/plain')
                                            self.end_headers()
                                            self.wfile.write(str(e).encode('utf-8'))

                                    def do_GET(self):
                                        path = self.path
                                        base = os.environ.get('KEYCLOAK_PROXY_TARGET', 'http://127.0.0.1:11000')
                                        p = urllib.parse.urlparse(base)
                                        kc_origin = f"{p.scheme}://{p.netloc}"
                                        client_scheme = self.headers.get('X-Forwarded-Proto') or ('https' if os.environ.get('CODESPACES') else 'http')
                                        client_host = self.headers.get('Host', '')
                                        client_origin = f"{client_scheme}://{client_host}" if client_host else ''
                                        strip = [kc_origin]
                                        if client_origin:
                                            strip.append(client_origin)

                                        if path.startswith('/keycloak/') or path.startswith('/keycloak?'):
                                            suffix = path[len('/keycloak'):]
                                            target = urllib.parse.urljoin(base, suffix)
                                            return self._proxy(target, method='GET', strip_origins=strip)

                                        if path.startswith('/realms/') or path.startswith('/resources/'):
                                            target = urllib.parse.urljoin(base, path)
                                            return self._proxy(target, method='GET', strip_origins=strip)

                                        if path.startswith('/proxy/') or path.startswith('/proxy?'):
                                            api = os.environ.get('API_PROXY_TARGET', 'http://127.0.0.1:8083')
                                            suffix = path[len('/proxy'):]
                                            target = urllib.parse.urljoin(api, suffix)
                                            return self._proxy(target, method='GET')

                                        if path == '/admin' or path.startswith('/admin/') or path.startswith('/admin?'):
                                            admin = os.environ.get('ADMIN_PROXY_TARGET', 'http://127.0.0.1:8081')
                                            suffix = path[len('/admin'):]
                                            target = urllib.parse.urljoin(admin, suffix)
                                            return self._proxy(target, method='GET')

                                        if path == '/customer' or path.startswith('/customer/') or path.startswith('/customer?'):
                                            cust = os.environ.get('CUSTOMER_PROXY_TARGET', 'http://127.0.0.1:8084')
                                            suffix = path[len('/customer'):]
                                            target = urllib.parse.urljoin(cust, suffix)
                                            return self._proxy(target, method='GET')

                                        if path == '/health':
                                            self.send_response(200)
                                            self.send_header('Content-Type', 'application/json')
                                            self.end_headers()
                                            self.wfile.write(b'{"status":"healthy"}')
                                            return

                                        return super().do_GET()

                                    def do_POST(self):
                                        length = int(self.headers.get('Content-Length', '0'))
                                        body = self.rfile.read(length) if length else None
                                        path = self.path

                                        base = os.environ.get('KEYCLOAK_PROXY_TARGET', 'http://127.0.0.1:11000')
                                        p = urllib.parse.urlparse(base)
                                        kc_origin = f"{p.scheme}://{p.netloc}"
                                        client_scheme = self.headers.get('X-Forwarded-Proto') or ('https' if os.environ.get('CODESPACES') else 'http')
                                        client_host = self.headers.get('Host', '')
                                        client_origin = f"{client_scheme}://{client_host}" if client_host else ''
                                        strip = [kc_origin]
                                        if client_origin:
                                            strip.append(client_origin)

                                        if path.startswith('/keycloak/') or path.startswith('/keycloak?'):
                                            suffix = path[len('/keycloak'):]
                                            target = urllib.parse.urljoin(base, suffix)
                                            return self._proxy(target, method='POST', body=body, strip_origins=strip)

                                        if path.startswith('/realms/') or path.startswith('/resources/'):
                                            target = urllib.parse.urljoin(base, path)
                                            return self._proxy(target, method='POST', body=body, strip_origins=strip)

                                        if path.startswith('/proxy/'):
                                            api = os.environ.get('API_PROXY_TARGET', 'http://127.0.0.1:8083')
                                            suffix = path[len('/proxy'):]
                                            target = urllib.parse.urljoin(api, suffix)
                                            return self._proxy(target, method='POST', body=body)

                                        if path.startswith('/admin'):
                                            admin = os.environ.get('ADMIN_PROXY_TARGET', 'http://127.0.0.1:8081')
                                            suffix = path[len('/admin'):]
                                            target = urllib.parse.urljoin(admin, suffix)
                                            return self._proxy(target, method='POST', body=body)

                                        if path.startswith('/customer'):
                                            cust = os.environ.get('CUSTOMER_PROXY_TARGET', 'http://127.0.0.1:8084')
                                            suffix = path[len('/customer'):]
                                            target = urllib.parse.urljoin(cust, suffix)
                                            return self._proxy(target, method='POST', body=body)

                                        self.send_response(404)
                                        self.end_headers()

                                    def end_headers(self):
                                        origin = self.headers.get('Origin')
                                        self.send_header('Access-Control-Allow-Origin', origin if origin else '*')
                                        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                                        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept, Accept-Language')
                                        self.send_header('Access-Control-Allow-Credentials', 'true')
                                        if origin:
                                            self.send_header('Vary', 'Origin')
                                        super().end_headers()

                                    def do_OPTIONS(self):
                                        self.send_response(204)
                                        self.end_headers()


                                def main(port=8082):
                                    os.chdir(os.path.dirname(__file__))
                                    server = HTTPServer(('', port), LandingHandler)
                                    print(f'Landing server listening on http://localhost:{port}')
                                    try:
                                        server.serve_forever()
                                    except KeyboardInterrupt:
                                        server.server_close()


                                if __name__ == '__main__':
                                    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
                                    main(port)
