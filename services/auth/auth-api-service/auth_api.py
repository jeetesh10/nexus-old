#!/usr/bin/env python3
"""
Auth API Service for Nexus Platform
Provides authentication endpoints for other services
"""
import json
import logging
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Keycloak configuration from environment variables
        self.keycloak_config = {
            'base_url': os.getenv('KEYCLOAK_BASE_URL', 'http://keycloak:8080'),
            'realm': os.getenv('KEYCLOAK_REALM', 'nexus-platform'),
            'client_id': os.getenv('KEYCLOAK_CLIENT_ID', 'nexus-platform'),
            'client_secret': os.getenv('KEYCLOAK_CLIENT_SECRET', ''),
            'admin_username': os.getenv('KEYCLOAK_ADMIN_USERNAME', ''),
            'admin_password': os.getenv('KEYCLOAK_ADMIN_PASSWORD', '')
        }
        
        # JWT configuration
        self.jwt_config = {
            'issuer': f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}",
            'audience': 'nexus-platform',
            'jwks_url': f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}/protocol/openid-connect/certs"
        }
        
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Set CORS headers
            self.send_cors_headers()
            
            # Route requests
            if path == '/api/auth/validate-token':
                token = query_params.get('token', [None])[0]
                self.validate_token(token)
            elif path == '/api/auth/user-info':
                token = query_params.get('token', [None])[0]
                self.get_user_info(token)
            elif path == '/api/auth/user-groups':
                token = query_params.get('token', [None])[0]
                self.get_user_groups(token)
            elif path == '/api/auth/health':
                self.get_health()
            elif path == '/api/auth/openid-config':
                self.get_openid_config()
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Set CORS headers
            self.send_cors_headers()
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            # Route requests
            if path == '/api/auth/login':
                username = data.get('username')
                password = data.get('password')
                self.login_user(username, password)
            elif path == '/api/auth/refresh-token':
                refresh_token = data.get('refresh_token')
                self.refresh_token(refresh_token)
            elif path == '/api/auth/logout':
                token = data.get('token')
                self.logout_user(token)
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def validate_token(self, token):
        """Validate JWT token"""
        try:
            if not token:
                self.send_error(400, "Token is required")
                return
            
            # Decode token without verification first to get header
            unverified_header = jwt.get_unverified_header(token)
            
            # Get public key from Keycloak
            jwks_client = PyJWKClient(self.jwt_config['jwks_url'])
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=self.jwt_config['audience'],
                issuer=self.jwt_config['issuer']
            )
            
            # Check if token is expired
            if 'exp' in payload and datetime.fromtimestamp(payload['exp']) < datetime.now():
                self.send_error(401, "Token expired")
                return
            
            response_data = {
                "valid": True,
                "user_id": payload.get('sub'),
                "username": payload.get('preferred_username'),
                "email": payload.get('email'),
                "exp": payload.get('exp'),
                "iat": payload.get('iat')
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except jwt.ExpiredSignatureError:
            self.send_error(401, "Token expired")
        except jwt.InvalidTokenError as e:
            self.send_error(401, f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            self.send_error(500, f"Token validation failed: {str(e)}")
    
    def get_user_info(self, token):
        """Get user information from token"""
        try:
            if not token:
                self.send_error(400, "Token is required")
                return
            
            # Validate token first
            unverified_header = jwt.get_unverified_header(token)
            jwks_client = PyJWKClient(self.jwt_config['jwks_url'])
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=self.jwt_config['audience'],
                issuer=self.jwt_config['issuer']
            )
            
            user_info = {
                "user_id": payload.get('sub'),
                "username": payload.get('preferred_username'),
                "email": payload.get('email'),
                "name": payload.get('name'),
                "given_name": payload.get('given_name'),
                "family_name": payload.get('family_name'),
                "groups": payload.get('groups', []),
                "roles": payload.get('realm_access', {}).get('roles', [])
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(user_info).encode())
            
        except Exception as e:
            logger.error(f"Get user info error: {e}")
            self.send_error(500, f"Failed to get user info: {str(e)}")
    
    def get_user_groups(self, token):
        """Get user groups from token"""
        try:
            if not token:
                self.send_error(400, "Token is required")
                return
            
            # Validate token and get user info
            unverified_header = jwt.get_unverified_header(token)
            jwks_client = PyJWKClient(self.jwt_config['jwks_url'])
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=self.jwt_config['audience'],
                issuer=self.jwt_config['issuer']
            )
            
            groups = payload.get('groups', [])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"groups": groups}).encode())
            
        except Exception as e:
            logger.error(f"Get user groups error: {e}")
            self.send_error(500, f"Failed to get user groups: {str(e)}")
    
    def login_user(self, username, password):
        """Login user and return tokens"""
        try:
            if not username or not password:
                self.send_error(400, "Username and password are required")
                return
            
            # Keycloak token endpoint
            token_url = f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}/protocol/openid-connect/token"
            
            data = {
                'grant_type': 'password',
                'client_id': self.keycloak_config['client_id'],
                'client_secret': self.keycloak_config['client_secret'],
                'username': username,
                'password': password
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                response_body = json.dumps(token_data).encode()
                
                # Send proper HTTP/1.1 response
                self.wfile.write(b"HTTP/1.1 200 OK\r\n")
                self.wfile.write(b"Content-Type: application/json\r\n")
                self.wfile.write(f"Content-Length: {len(response_body)}\r\n".encode())
                self.wfile.write(b"\r\n")
                self.wfile.write(response_body)
            else:
                error_data = {"error": "Invalid credentials"}
                response_body = json.dumps(error_data).encode()
                
                # Send proper HTTP/1.1 error response
                self.wfile.write(b"HTTP/1.1 401 Unauthorized\r\n")
                self.wfile.write(b"Content-Type: application/json\r\n")
                self.wfile.write(f"Content-Length: {len(response_body)}\r\n".encode())
                self.wfile.write(b"\r\n")
                self.wfile.write(response_body)
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.send_error(500, f"Login failed: {str(e)}")
    
    def refresh_token(self, refresh_token):
        """Refresh access token"""
        try:
            if not refresh_token:
                self.send_error(400, "Refresh token is required")
                return
            
            # Keycloak token endpoint
            token_url = f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}/protocol/openid-connect/token"
            
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.keycloak_config['client_id'],
                'client_secret': self.keycloak_config['client_secret'],
                'refresh_token': refresh_token
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(token_data).encode())
            else:
                self.send_error(401, "Invalid refresh token")
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            self.send_error(500, f"Token refresh failed: {str(e)}")
    
    def logout_user(self, token):
        """Logout user"""
        try:
            if not token:
                self.send_error(400, "Token is required")
                return
            
            # Keycloak logout endpoint
            logout_url = f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}/protocol/openid-connect/logout"
            
            data = {
                'client_id': self.keycloak_config['client_id'],
                'client_secret': self.keycloak_config['client_secret'],
                'refresh_token': token
            }
            
            response = requests.post(logout_url, data=data, timeout=10)
            
            if response.status_code == 204:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Logged out successfully"}).encode())
            else:
                self.send_error(400, "Logout failed")
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self.send_error(500, f"Logout failed: {str(e)}")
    
    def get_openid_config(self):
        """Get OpenID Connect configuration"""
        try:
            config_url = f"{self.keycloak_config['base_url']}/realms/{self.keycloak_config['realm']}/.well-known/openid_configuration"
            response = requests.get(config_url, timeout=10)
            
            if response.status_code == 200:
                config_data = response.json()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(config_data).encode())
            else:
                self.send_error(500, "Failed to get OpenID configuration")
                
        except Exception as e:
            logger.error(f"OpenID config error: {e}")
            self.send_error(500, f"Failed to get OpenID configuration: {str(e)}")
    
    def get_health(self):
        """Health check endpoint"""
        try:
            health_data = {
                "status": "healthy",
                "service": "auth-api",
                "version": "1.0.0"
            }
            
            response_body = json.dumps(health_data).encode()
            
            # Send proper HTTP/1.1 response
            self.wfile.write(b"HTTP/1.1 200 OK\r\n")
            self.wfile.write(b"Content-Type: application/json\r\n")
            self.wfile.write(f"Content-Length: {len(response_body)}\r\n".encode())
            self.wfile.write(b"\r\n")
            self.wfile.write(response_body)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            error_data = {"status": "unhealthy", "error": str(e)}
            response_body = json.dumps(error_data).encode()
            
            # Send proper HTTP/1.1 error response
            self.wfile.write(b"HTTP/1.1 500 Internal Server Error\r\n")
            self.wfile.write(b"Content-Type: application/json\r\n")
            self.wfile.write(f"Content-Length: {len(response_body)}\r\n".encode())
            self.wfile.write(b"\r\n")
            self.wfile.write(response_body)
    
    def log_message(self, format, *args):
        """Custom logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_auth_api(port=8084):
    """Run the Auth API service"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, AuthAPIHandler)
        logger.info(f"🔐 Auth API Service running on port {port}")
        logger.info(f"📊 Health check: http://localhost:{port}/api/auth/health")
        logger.info(f"🔑 Token validation: http://localhost:{port}/api/auth/validate-token")
        logger.info(f"👤 User info: http://localhost:{port}/api/auth/user-info")
        logger.info(f"👥 User groups: http://localhost:{port}/api/auth/user-groups")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Auth API stopped by user")
    except Exception as e:
        logger.error(f"Auth API error: {e}")

if __name__ == "__main__":
    run_auth_api()
