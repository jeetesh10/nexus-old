import httpx
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Configuration
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api-service:8084")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

class AuthMiddleware:
    def __init__(self):
        self.auth_api_url = AUTH_API_URL
        self.jwt_secret = JWT_SECRET
    
    async def validate_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Validate JWT token and return user info"""
        try:
            token = credentials.credentials
            
            # First, try to validate with Auth API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_api_url}/api/auth/validate-token",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info(f"Token validated for user: {user_info.get('username')}")
                    return user_info
                else:
                    logger.warning(f"Token validation failed: {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Auth API connection error: {e}")
            # Fallback to local JWT validation
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                return payload
            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def require_auth(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Require authentication for protected endpoints"""
        return await self.validate_token(credentials)
    
    async def require_admin(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Require admin role for admin-only endpoints"""
        user_info = await self.validate_token(credentials)
        
        # Check if user has admin role
        roles = user_info.get('roles', [])
        if 'platform-admin' not in roles and 'admin' not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return user_info
    
    async def get_user_service_access(self, credentials: HTTPAuthorizationCredentials = Depends(security), service_name: str = None) -> Dict[str, Any]:
        """Check if user has access to specific service"""
        user_info = await self.validate_token(credentials)
        
        # If service_name is provided, check service-specific access
        if service_name:
            groups = user_info.get('groups', [])
            # Check if user has access to the service
            # This could be enhanced with more granular permissions
            if not any(group.endswith(f"-{service_name}") or group == "platform-admin" for group in groups):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to service: {service_name}"
                )
        
        return user_info

# Global auth middleware instance
auth_middleware = AuthMiddleware()
