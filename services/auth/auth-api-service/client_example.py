#!/usr/bin/env python3
"""
Example client integration for Auth API Service
Shows how other services can integrate with the auth API
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthAPIClient:
    def __init__(self, base_url="http://localhost:8084"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def validate_token(self, token):
        """Validate JWT token"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/validate-token",
                params={"token": token},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token validation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def get_user_info(self, token):
        """Get user information from token"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/user-info",
                params={"token": token},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get user info failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Get user info error: {e}")
            return None
    
    def get_user_groups(self, token):
        """Get user groups from token"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/user-groups",
                params={"token": token},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()["groups"]
            else:
                logger.error(f"Get user groups failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Get user groups error: {e}")
            return []
    
    def login_user(self, username, password):
        """Login user and get tokens"""
        try:
            data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Login failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None
    
    def refresh_token(self, refresh_token):
        """Refresh access token"""
        try:
            data = {
                "refresh_token": refresh_token
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/refresh-token",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def logout_user(self, refresh_token):
        """Logout user"""
        try:
            data = {
                "token": refresh_token
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/logout",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Logout failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def check_health(self):
        """Check service health"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/health",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return None

# Example usage in a service
class ExampleService:
    def __init__(self):
        self.auth_client = AuthAPIClient()
    
    def handle_request(self, request_headers):
        """Handle incoming request with authentication"""
        # Extract token from Authorization header
        auth_header = request_headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {"error": "Missing or invalid Authorization header"}, 401
        
        token = auth_header.split(' ')[1]
        
        # Validate token
        token_info = self.auth_client.validate_token(token)
        if not token_info:
            return {"error": "Invalid token"}, 401
        
        # Get user information
        user_info = self.auth_client.get_user_info(token)
        if not user_info:
            return {"error": "Failed to get user info"}, 500
        
        # Get user groups for authorization
        user_groups = self.auth_client.get_user_groups(token)
        
        # Check if user has required permissions
        if not self.has_permission(user_groups, "admin-dashboard"):
            return {"error": "Insufficient permissions"}, 403
        
        # Process the request
        return self.process_request(user_info)
    
    def has_permission(self, user_groups, required_service):
        """Check if user has permission to access service"""
        # This would typically check against your access control service
        # For now, we'll do a simple check
        required_groups = [
            f"nexus/{required_service}",
            "nexus/platform-admin",
            "nexus/service-admin"
        ]
        
        return any(group in user_groups for group in required_groups)
    
    def process_request(self, user_info):
        """Process the authenticated request"""
        return {
            "message": "Request processed successfully",
            "user": user_info["username"],
            "timestamp": "2024-01-01T00:00:00Z"
        }

# Example middleware for FastAPI
def auth_middleware(request, call_next):
    """FastAPI middleware for authentication"""
    auth_client = AuthAPIClient()
    
    # Extract token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401
    
    token = auth_header.split(' ')[1]
    
    # Validate token
    token_info = auth_client.validate_token(token)
    if not token_info:
        return {"error": "Invalid token"}, 401
    
    # Add user info to request state
    request.state.user_info = auth_client.get_user_info(token)
    request.state.user_groups = auth_client.get_user_groups(token)
    
    # Continue with the request
    response = call_next(request)
    return response

# Example usage
if __name__ == "__main__":
    # Test the client
    client = AuthAPIClient()
    
    # Check health
    health = client.check_health()
    if health:
        print("✅ Auth API Service is healthy")
        print(f"Status: {health['status']}")
        print(f"Keycloak: {health['keycloak']}")
    else:
        print("❌ Auth API Service is not responding")
    
    # Example login (you would need valid credentials)
    # login_result = client.login_user("admin", "AdminPass123")
    # if login_result:
    #     token = login_result["access_token"]
    #     
    #     # Validate token
    #     token_info = client.validate_token(token)
    #     print(f"Token valid: {token_info is not None}")
    #     
    #     # Get user info
    #     user_info = client.get_user_info(token)
    #     print(f"User: {user_info['username'] if user_info else 'Unknown'}")
    #     
    #     # Get user groups
    #     groups = client.get_user_groups(token)
    #     print(f"Groups: {groups}")
