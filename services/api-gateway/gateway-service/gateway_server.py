#!/usr/bin/env python3
"""
API Gateway for Nexus Platform
Single entry point for all external clients
"""
import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from datetime import datetime
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GatewayHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Service configurations
        self.services = {
            'access-control': {
                'host': 'localhost',
                'port': 8083,
                'health_path': '/api/health',
            },
            'auth-api': {
                'host': 'localhost',
                'port': 8084,
                'health_path': '/api/auth/health',
            },
            'landing-page': {
                'host': 'localhost',
                'port': 8082,
                'health_path': '/health',
            },
            'admin-dashboard': {
                'host': 'localhost',
                'port': 8081,
                'health_path': '/health',
            },
            'keycloak': {
                'host': 'localhost',
                'port': 8080,
                'health_path': '/realms/nexus-platform',
            },
        }
        
        # Security configuration
        self.allowed_ips = [
            ipaddress.ip_network('127.0.0.0/8'),  # Localhost
            ipaddress.ip_network('10.0.0.0/8'),   # Internal network
            ipaddress.ip_network('172.16.0.0/12'), # Docker network
            ipaddress.ip_network('192.168.0.0/16') # Local network
        ]
        
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Check IP restrictions
            if not self.is_ip_allowed():
                self.send_error(403, "Access denied")
                return
            
            # Set CORS headers
            self.send_cors_headers()
            
            # Parse request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Route request
            self.route_request(path, query_params)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Check IP restrictions
            if not self.is_ip_allowed():
                self.send_error(403, "Access denied")
                return
            
            # Set CORS headers
            self.send_cors_headers()
            
            # Parse request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Route request
            self.route_request(path, {})
            
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def is_ip_allowed(self):
        """Check if client IP is allowed"""
        client_ip = ipaddress.ip_address(self.client_address[0])
        return any(client_ip in network for network in self.allowed_ips)
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def route_request(self, path, query_params):
        """Route request to appropriate service"""
        logger.info(f"Routing request: {path} from {self.client_address[0]}")
        
        # Health check endpoint
        if path == '/health':
            self.get_health()
            return
        
        # API routes (Access Control Service)
        if path.startswith('/api/'):
            self.proxy_to_service('access-control', path, query_params)
            return
        
        # Auth API routes (for other services)
        if path.startswith('/api/auth/'):
            self.proxy_to_service('auth-api', path, query_params)
            return
        
        # Auth routes (Keycloak)
        if path.startswith('/auth/') or path.startswith('/realms/'):
            self.proxy_to_service('keycloak', path, query_params)
            return
        
        # Admin routes (Admin Dashboard)
        if path.startswith('/admin/'):
            self.proxy_to_service('admin-dashboard', path, query_params)
            return
        
        # Landing page routes
        if path.startswith('/landing') or path in ['/', '/login.html', '/landing-page.html']:
            self.proxy_to_service('landing-page', path, query_params)
            return
        
        # Default: return 404
        self.send_error(404, "Endpoint not found")
    
    def proxy_to_service(self, service_name, path, query_params):
        """Proxy request to internal service"""
        try:
            service = self.services[service_name]
            
            # Build target URL
            query_string = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
            target_url = f"http://{service['host']}:{service['port']}{path}"
            if query_string:
                target_url += f"?{query_string}"
            
            logger.info(f"Proxying to {service_name}: {target_url}")
            
            # Forward request
            response = requests.get(target_url, timeout=10)
            
            # Forward response
            self.send_response(response.status_code)
            
            # Forward headers
            for header, value in response.headers.items():
                if header.lower() not in ['transfer-encoding', 'connection']:
                    self.send_header(header, value)
            
            self.send_cors_headers()
            self.end_headers()
            
            # Forward body
            self.wfile.write(response.content)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error proxying to {service_name}: {e}")
            self.send_error(502, f"Service {service_name} unavailable")
    
    def get_health(self):
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "gateway": "running",
                "services": {}
            }
            
            # Check service health
            for service_name, service in self.services.items():
                health_url = f"http://{service['host']}:{service['port']}{service.get('health_path', '/health')}"
                try:
                    response = requests.get(health_url, timeout=5)
                    health_data["services"][service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds(),
                        "http_code": response.status_code
                    }
                except Exception as e:
                    health_data["services"][service_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(health_data, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.send_error(500, f"Health check failed: {str(e)}")
    
    def log_message(self, format, *args):
        """Custom logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_gateway(port=8080):
    """Run the API Gateway"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, GatewayHandler)
        logger.info(f"🚀 API Gateway running on port {port}")
        logger.info(f"📊 Health check: http://localhost:{port}/health")
        logger.info(f"🔗 External access: http://localhost:{port}/api/*")
        logger.info(f"🔐 Auth access: http://localhost:{port}/auth/*")
        logger.info(f"🏠 Landing page: http://localhost:{port}/landing")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Gateway stopped by user")
    except Exception as e:
        logger.error(f"Gateway error: {e}")

if __name__ == "__main__":
    run_gateway()
