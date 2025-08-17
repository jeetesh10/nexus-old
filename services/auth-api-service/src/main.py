#!/usr/bin/env python3
"""
Auth API Service for Nexus Platform
JWT validation and group-based authorization service
"""

import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import jwt
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Nexus Auth API Service",
    description="JWT validation and group-based authorization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    KEYCLOAK_BASE_URL = os.getenv('KEYCLOAK_BASE_URL', 'http://localhost:8080')
    KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'nexus-platform')
    KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'nexus-client')
    KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET', '')
    KEYCLOAK_ADMIN_USERNAME = os.getenv('KEYCLOAK_ADMIN_USERNAME', 'admin')
    KEYCLOAK_ADMIN_PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin')
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8085'))
    
    @property
    def jwks_url(self):
        return f"{self.KEYCLOAK_BASE_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    
    @property
    def issuer(self):
        return f"{self.KEYCLOAK_BASE_URL}/realms/{self.KEYCLOAK_REALM}"
    
    @property
    def token_url(self):
        return f"{self.KEYCLOAK_BASE_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/token"
    
    @property
    def admin_url(self):
        return f"{self.KEYCLOAK_BASE_URL}/admin/realms/{self.KEYCLOAK_REALM}"

config = Config()

# Pydantic models
class AuthValidationRequest(BaseModel):
    jwt_token: str = Field(..., description="JWT token from Keycloak")
    resource: str = Field(..., description="Resource being accessed (e.g., 'id-service')")
    client_context: str = Field(default="nexus", description="Client context (e.g., 'acmy', 'nexus')")
    action: str = Field(default="read", description="Action being performed (e.g., 'read', 'write')")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    client_context: str = Field(default="nexus", description="Client context")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_info: Dict[str, Any]

class CreateUserRequest(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    groups: List[str] = Field(default_factory=list, description="List of groups to assign")

class GroupRequest(BaseModel):
    group_name: str = Field(..., description="Group name in format: Client/Service/Type/Name")
    description: Optional[str] = None

class UserGroupRequest(BaseModel):
    username: str = Field(..., description="Username")
    group_name: str = Field(..., description="Group name")

class UserPermissions(BaseModel):
    role: Optional[str] = None
    subscription: Optional[str] = None
    features: List[str] = []
    has_access: bool = False

class AuthValidationResponse(BaseModel):
    valid: bool
    allowed: bool
    permissions: UserPermissions
    user_context: Dict[str, Any]
    expires_at: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    keycloak_status: str
    service_info: Dict[str, Any]

# Auth Service Class
class AuthService:
    def __init__(self):
        self.jwks_client = None
        self._jwks_cache = {}
        self._jwks_last_fetch = None
        
    def get_public_keys(self):
        """Get Keycloak public keys for JWT validation"""
        try:
            if not self._jwks_cache or self._should_refresh_jwks():
                logger.info(f"Fetching JWKS from {config.jwks_url}")
                response = requests.get(config.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_last_fetch = datetime.now()
                logger.info("JWKS cache updated successfully")
            
            return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise HTTPException(status_code=503, detail="Cannot connect to Keycloak")
    
    def _should_refresh_jwks(self):
        """Check if JWKS cache should be refreshed (every 5 minutes)"""
        if not self._jwks_last_fetch:
            return True
        return (datetime.now() - self._jwks_last_fetch).seconds > 300
    
    def validate_jwt(self, token: str) -> Dict[str, Any]:
        """Validate JWT token signature and claims"""
        try:
            # Get unverified header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise ValueError("Token missing key ID")
            
            # Get public keys
            jwks = self.get_public_keys()
            
            # Find the right key
            public_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    break
            
            if not public_key:
                raise ValueError(f"Public key not found for kid: {kid}")
            
            # Validate and decode token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                issuer=config.issuer,
                options={"verify_aud": False}  # We'll validate audience manually if needed
            )
            
            # Check expiration manually for better error messages
            if 'exp' in payload:
                exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
                if exp_time < datetime.now(tz=timezone.utc):
                    raise ValueError("Token has expired")
            
            logger.info(f"JWT validated successfully for user: {payload.get('preferred_username', 'unknown')}")
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise ValueError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            raise ValueError(f"Token validation failed: {e}")
    
    def parse_groups(self, groups: List[str], client_context: str, resource: str) -> UserPermissions:
        """Parse user groups to extract permissions for specific client and resource"""
        try:
            logger.debug(f"Parsing groups for client: {client_context}, resource: {resource}")
            logger.debug(f"User groups: {groups}")
            
            # Filter groups for the specific client and resource
            # Expected format: "Client/Service/Role/RoleName" or "Client/Service/Subscription/Level"
            client_resource_groups = []
            
            # Handle both exact matches and variations
            possible_patterns = [
                f"{client_context}/{resource}/",
                f"{client_context.title()}/{resource}/",
                f"{client_context.lower()}/{resource}/",
                f"{client_context}/{resource.replace('-', ' ')}/",
                f"{client_context.title()}/{resource.replace('-', ' ').title()}/"
            ]
            
            for group in groups:
                for pattern in possible_patterns:
                    if pattern.lower() in group.lower():
                        client_resource_groups.append(group)
                        break
            
            if not client_resource_groups:
                # Check for Nexus internal access
                nexus_patterns = ["nexus/", "Nexus/"]
                for group in groups:
                    for pattern in nexus_patterns:
                        if group.startswith(pattern):
                            client_resource_groups.append(group)
                            break
            
            logger.debug(f"Filtered groups: {client_resource_groups}")
            
            # Extract role and subscription
            role = self._extract_role(client_resource_groups)
            subscription = self._extract_subscription(client_resource_groups)
            features = self._get_features(role, subscription)
            
            has_access = len(client_resource_groups) > 0 or self._has_nexus_access(groups)
            
            permissions = UserPermissions(
                role=role,
                subscription=subscription,
                features=features,
                has_access=has_access
            )
            
            logger.info(f"Parsed permissions: role={role}, subscription={subscription}, access={has_access}")
            return permissions
            
        except Exception as e:
            logger.error(f"Error parsing groups: {e}")
            return UserPermissions(has_access=False)
    
    def _extract_role(self, groups: List[str]) -> Optional[str]:
        """Extract role from groups"""
        for group in groups:
            if "/Role/" in group or "/role/" in group:
                parts = group.split("/")
                for i, part in enumerate(parts):
                    if part.lower() == "role" and i + 1 < len(parts):
                        return parts[i + 1].lower()
        return None
    
    def _extract_subscription(self, groups: List[str]) -> Optional[str]:
        """Extract subscription level from groups"""
        for group in groups:
            if "/Subscription/" in group or "/subscription/" in group:
                parts = group.split("/")
                for i, part in enumerate(parts):
                    if part.lower() == "subscription" and i + 1 < len(parts):
                        return parts[i + 1].lower()
        return None
    
    def _has_nexus_access(self, groups: List[str]) -> bool:
        """Check if user has Nexus internal access"""
        nexus_groups = ["nexus/employee", "nexus/admin", "nexus/platform-admin"]
        for group in groups:
            if any(nexus_group in group.lower() for nexus_group in nexus_groups):
                return True
        return False
    
    def _get_features(self, role: Optional[str], subscription: Optional[str]) -> List[str]:
        """Get available features based on role and subscription"""
        features = []
        
        # Role-based features
        if role == "admin":
            features.extend(["admin-access", "user-management", "full-control"])
        elif role == "customer":
            features.extend(["basic-access", "read-operations"])
        
        # Subscription-based features
        if subscription == "pro+":
            features.extend(["bulk-operations", "webhooks", "priority-support", "advanced-analytics"])
        elif subscription == "pro":
            features.extend(["bulk-operations", "webhooks", "standard-support"])
        elif subscription == "basic":
            features.extend(["standard-operations", "basic-support"])
        
        return list(set(features))  # Remove duplicates
    
    def check_action_permission(self, permissions: UserPermissions, action: str) -> bool:
        """Check if the given action is allowed based on permissions"""
        if not permissions.has_access:
            return False
        
        # Define action permissions
        action_requirements = {
            "read": ["basic-access", "admin-access"],
            "write": ["admin-access", "full-control"],
            "delete": ["admin-access", "full-control"],
            "admin": ["admin-access", "full-control"]
        }
        
        required_features = action_requirements.get(action.lower(), ["basic-access"])
        return any(feature in permissions.features for feature in required_features)
    
    def check_keycloak_health(self) -> str:
        """Check if Keycloak is accessible"""
        try:
            response = requests.get(config.jwks_url, timeout=5)
            response.raise_for_status()
            return "healthy"
        except Exception as e:
            logger.warning(f"Keycloak health check failed: {e}")
            return "unhealthy"
    
    def get_admin_token(self) -> str:
        """Get admin access token from Keycloak"""
        try:
            token_url = f"{config.KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token"
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': config.KEYCLOAK_ADMIN_USERNAME,
                'password': config.KEYCLOAK_ADMIN_PASSWORD
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            return token_data['access_token']
            
        except Exception as e:
            logger.error(f"Failed to get admin token: {e}")
            raise HTTPException(status_code=503, detail="Cannot authenticate with Keycloak admin")
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get JWT token"""
        try:
            data = {
                'grant_type': 'password',
                'client_id': config.KEYCLOAK_CLIENT_ID,
                'username': username,
                'password': password,
                'scope': 'openid profile email'
            }
            
            if config.KEYCLOAK_CLIENT_SECRET:
                data['client_secret'] = config.KEYCLOAK_CLIENT_SECRET
            
            response = requests.post(config.token_url, data=data, timeout=10)
            
            if response.status_code == 401:
                raise ValueError("Invalid username or password")
            
            response.raise_for_status()
            token_data = response.json()
            
            # Get user info from token
            user_info = self.validate_jwt(token_data['access_token'])
            
            return {
                'access_token': token_data['access_token'],
                'token_type': 'bearer',
                'expires_in': token_data.get('expires_in', 3600),
                'refresh_token': token_data.get('refresh_token'),
                'user_info': {
                    'user_id': user_info.get('sub'),
                    'username': user_info.get('preferred_username'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'groups': user_info.get('groups', [])
                }
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise ValueError(f"Login failed: {e}")
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: Optional[str] = None, last_name: Optional[str] = None,
                   groups: List[str] = None) -> Dict[str, Any]:
        """Create a new user in Keycloak"""
        try:
            admin_token = self.get_admin_token()
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            user_data = {
                'username': username,
                'email': email,
                'enabled': True,
                'emailVerified': True,
                'credentials': [{
                    'type': 'password',
                    'value': password,
                    'temporary': False
                }]
            }
            
            if first_name:
                user_data['firstName'] = first_name
            if last_name:
                user_data['lastName'] = last_name
            
            # Create user
            create_url = f"{config.admin_url}/users"
            response = requests.post(create_url, json=user_data, headers=headers, timeout=10)
            
            if response.status_code == 409:
                raise ValueError(f"User {username} already exists")
            
            response.raise_for_status()
            
            # Get the created user ID
            user_id = self._get_user_id(username, admin_token)
            
            # Add user to groups if specified
            if groups:
                for group_name in groups:
                    try:
                        self._add_user_to_group(user_id, group_name, admin_token)
                    except Exception as e:
                        logger.warning(f"Failed to add user to group {group_name}: {e}")
            
            logger.info(f"User {username} created successfully")
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'groups': groups or []
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise ValueError(f"User creation failed: {e}")
    
    def create_group(self, group_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new group in Keycloak"""
        try:
            admin_token = self.get_admin_token()
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Parse group path (create parent groups if needed)
            group_parts = group_name.split('/')
            current_path = ""
            
            for part in group_parts:
                current_path += f"/{part}" if current_path else part
                
                # Check if group exists
                if not self._group_exists(current_path, admin_token):
                    group_data = {
                        'name': part,
                        'path': f"/{current_path}"
                    }
                    
                    if current_path == group_name and description:
                        group_data['attributes'] = {'description': [description]}
                    
                    create_url = f"{config.admin_url}/groups"
                    response = requests.post(create_url, json=group_data, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    logger.info(f"Group {current_path} created")
            
            return {
                'group_name': group_name,
                'description': description,
                'path': f"/{group_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            raise ValueError(f"Group creation failed: {e}")
    
    def add_user_to_group(self, username: str, group_name: str) -> Dict[str, Any]:
        """Add user to a group"""
        try:
            admin_token = self.get_admin_token()
            user_id = self._get_user_id(username, admin_token)
            self._add_user_to_group(user_id, group_name, admin_token)
            
            return {
                'username': username,
                'group_name': group_name,
                'status': 'added'
            }
            
        except Exception as e:
            logger.error(f"Failed to add user to group: {e}")
            raise ValueError(f"Failed to add user to group: {e}")
    
    def _get_user_id(self, username: str, admin_token: str) -> str:
        """Get user ID by username"""
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{config.admin_url}/users?username={username}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        users = response.json()
        if not users:
            raise ValueError(f"User {username} not found")
        
        return users[0]['id']
    
    def _group_exists(self, group_path: str, admin_token: str) -> bool:
        """Check if group exists"""
        try:
            headers = {'Authorization': f'Bearer {admin_token}'}
            search_url = f"{config.admin_url}/groups"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            groups = response.json()
            return any(group.get('path') == f"/{group_path}" for group in groups)
            
        except Exception:
            return False
    
    def _add_user_to_group(self, user_id: str, group_name: str, admin_token: str):
        """Add user to group by group name"""
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        # Get group ID
        group_id = self._get_group_id(group_name, admin_token)
        
        # Add user to group
        add_url = f"{config.admin_url}/users/{user_id}/groups/{group_id}"
        response = requests.put(add_url, headers=headers, timeout=10)
        response.raise_for_status()
    
    def _get_group_id(self, group_name: str, admin_token: str) -> str:
        """Get group ID by group name/path"""
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{config.admin_url}/groups"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        groups = response.json()
        for group in groups:
            if group.get('path') == f"/{group_name}" or group.get('name') == group_name:
                return group['id']
        
        raise ValueError(f"Group {group_name} not found")

# Initialize auth service
auth_service = AuthService()

# API Routes
@app.post("/api/auth/validate", response_model=AuthValidationResponse)
async def validate_auth(request: AuthValidationRequest):
    """Validate JWT token and check authorization"""
    try:
        # Validate JWT
        jwt_payload = auth_service.validate_jwt(request.jwt_token)
        
        # Extract user groups
        user_groups = jwt_payload.get('groups', [])
        
        # Parse permissions
        permissions = auth_service.parse_groups(
            user_groups, 
            request.client_context, 
            request.resource
        )
        
        # Check action permission
        action_allowed = auth_service.check_action_permission(permissions, request.action)
        
        # Build user context
        user_context = {
            "user_id": jwt_payload.get('sub'),
            "email": jwt_payload.get('email'),
            "username": jwt_payload.get('preferred_username'),
            "client_context": request.client_context,
            "groups": user_groups
        }
        
        # Get expiration time
        expires_at = None
        if 'exp' in jwt_payload:
            expires_at = datetime.fromtimestamp(jwt_payload['exp'], tz=timezone.utc).isoformat()
        
        return AuthValidationResponse(
            valid=True,
            allowed=action_allowed,
            permissions=permissions,
            user_context=user_context,
            expires_at=expires_at
        )
        
    except ValueError as e:
        logger.warning(f"Validation failed: {e}")
        return AuthValidationResponse(
            valid=False,
            allowed=False,
            permissions=UserPermissions(has_access=False),
            user_context={},
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in validation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/user-permissions")
async def get_user_permissions(token: str):
    """Get all permissions for a user (convenience endpoint)"""
    try:
        jwt_payload = auth_service.validate_jwt(token)
        user_groups = jwt_payload.get('groups', [])
        
        return {
            "user_id": jwt_payload.get('sub'),
            "email": jwt_payload.get('email'),
            "username": jwt_payload.get('preferred_username'),
            "groups": user_groups,
            "expires_at": datetime.fromtimestamp(jwt_payload.get('exp', 0), tz=timezone.utc).isoformat() if jwt_payload.get('exp') else None
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user and get JWT token"""
    try:
        result = auth_service.login_user(request.username, request.password)
        return LoginResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/users")
async def create_user(request: CreateUserRequest):
    """Create a new user (for testing purposes)"""
    try:
        result = auth_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            groups=request.groups
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/groups")
async def create_group(request: GroupRequest):
    """Create a new group (for testing purposes)"""
    try:
        result = auth_service.create_group(request.group_name, request.description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Group creation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/user-groups")
async def add_user_to_group(request: UserGroupRequest):
    """Add user to a group (for testing purposes)"""
    try:
        result = auth_service.add_user_to_group(request.username, request.group_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Add user to group error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    keycloak_status = auth_service.check_keycloak_health()
    
    return HealthResponse(
        status="healthy" if keycloak_status == "healthy" else "degraded",
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        keycloak_status=keycloak_status,
        service_info={
            "name": "auth-api-service",
            "version": "1.0.0",
            "port": config.SERVICE_PORT,
            "keycloak_url": config.KEYCLOAK_BASE_URL,
            "realm": config.KEYCLOAK_REALM
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Nexus Auth API Service",
        "status": "running",
        "docs": "/docs",
        "health": "/api/auth/health"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Nexus Auth API Service")
    logger.info(f"Keycloak URL: {config.KEYCLOAK_BASE_URL}")
    logger.info(f"Realm: {config.KEYCLOAK_REALM}")
    logger.info(f"Service Port: {config.SERVICE_PORT}")
    
    # Test Keycloak connection
    keycloak_status = auth_service.check_keycloak_health()
    logger.info(f"Keycloak status: {keycloak_status}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=True,
        log_level="info"
    )
