#!/usr/bin/env python3
"""
Optimized API Gateway for Nexus Platform
Handles external traffic only, delegates internal routing to service mesh
"""
import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from datetime import datetime
import ipaddress
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedGatewayHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # External service configurations (only client-facing)
        self.external_services = {
            'landing-page': {
                'host': 'localhost',
                'port': 8082,
                'base_path': '/landing'
            },
            'auth': {
                'host': 'localhost',
                'port': 8080,
                'base_path': '/realms/nexus-platform'
            }
        }
        
        # Internal service discovery (for service mesh)
        self.internal_services = {
            'access-control': 'localhost:8083',
            'auth-api': 'localhost:8084',
            'admin-dashboard': 'localhost:8081'
        }
        
        # Security configuration
        self.allowed_ips = [
            ipaddress.ip_network('127.0.0.0/8'),  # Localhost
            ipaddress.ip_network('10.0.0.0/8'),   # Internal network
            ipaddress.ip_network('172.16.0.0/12'), # Docker network
            ipaddress.ip_network('192.168.0.0/16') # Local network
        ]
        
        # Performance configuration
        self.connection_pool = aiohttp.ClientSession()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
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
        
        # External routes (client-facing only)
        if path.startswith('/landing') or path in ['/', '/login.html', '/landing-page.html']:
            self.proxy_to_external_service('landing-page', path, query_params)
            return
        
        # Auth routes (external Keycloak access)
        if path.startswith('/auth/') or path.startswith('/realms/'):
            self.proxy_to_external_service('auth', path, query_params)
            return
        
        # Internal API routes (delegate to service mesh)
        if path.startswith('/api/'):
            self.delegate_to_service_mesh(path, query_params)
            return
        
        # Default: return 404
        self.send_error(404, "Endpoint not found")
    
    def proxy_to_external_service(self, service_name, path, query_params):
        """Proxy request to external service"""
        try:
            service = self.external_services[service_name]
            
            # Build target URL
            query_string = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
            target_url = f"http://{service['host']}:{service['port']}{path}"
            if query_string:
                target_url += f"?{query_string}"
            
            logger.info(f"Proxying to external service {service_name}: {target_url}")
            
            # Forward request with optimized connection pooling
            response = requests.get(target_url, timeout=5)
            
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
            logger.error(f"Error proxying to external service {service_name}: {e}")
            self.send_error(502, f"External service {service_name} unavailable")
    
    def delegate_to_service_mesh(self, path, query_params):
        """Delegate internal requests to service mesh"""
        try:
            # Extract service name from path
            # /api/auth/validate-token -> auth-api
            # /api/services -> access-control
            path_parts = path.split('/')
            if len(path_parts) >= 3:
                service_type = path_parts[2]  # 'auth' or 'services'
                
                if service_type == 'auth':
                    service_name = 'auth-api'
                elif service_type == 'services':
                    service_name = 'access-control'
                else:
                    service_name = 'access-control'  # default
                
                service_url = self.internal_services.get(service_name)
                if service_url:
                    # Build target URL
                    query_string = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
                    target_url = f"http://{service_url}{path}"
                    if query_string:
                        target_url += f"?{query_string}"
                    
                    logger.info(f"Delegating to service mesh {service_name}: {target_url}")
                    
                    # Use optimized connection for internal calls
                    response = requests.get(target_url, timeout=3)
                    
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
                else:
                    self.send_error(503, f"Service {service_name} not available in mesh")
            else:
                self.send_error(400, "Invalid API path")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error delegating to service mesh: {e}")
            self.send_error(502, "Service mesh unavailable")
    
    def get_health(self):
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "gateway": "optimized",
                "external_services": {},
                "internal_services": {}
            }
            
            # Check external service health
            for service_name, service in self.external_services.items():
                try:
                    health_url = f"http://{service['host']}:{service['port']}/health"
                    response = requests.get(health_url, timeout=2)
                    health_data["external_services"][service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                    }
                except Exception as e:
                    health_data["external_services"][service_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            
            # Check internal service health
            for service_name, service_url in self.internal_services.items():
                try:
                    health_url = f"http://{service_url}/health"
                    response = requests.get(health_url, timeout=2)
                    health_data["internal_services"][service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                    }
                except Exception as e:
                    health_data["internal_services"][service_name] = {
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

def run_optimized_gateway(port=8080):
    """Run the optimized API Gateway"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, OptimizedGatewayHandler)
        logger.info(f"🚀 Optimized API Gateway running on port {port}")
        logger.info(f"📊 Health check: http://localhost:{port}/health")
        logger.info(f"🔗 External access: http://localhost:{port}/landing")
        logger.info(f"🔐 Auth access: http://localhost:{port}/auth/*")
        logger.info(f"🕸️ Internal delegation: http://localhost:{port}/api/*")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Optimized Gateway stopped by user")
    except Exception as e:
        logger.error(f"Optimized Gateway error: {e}")

if __name__ == "__main__":
    run_optimized_gateway()
