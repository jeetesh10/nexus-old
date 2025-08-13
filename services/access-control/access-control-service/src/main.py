from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import asyncio
import logging
from datetime import datetime
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Access Control Service",
    description="User and Group Management using MongoDB as managed service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGODB_ORCHESTRATOR_URL = os.getenv("MONGODB_ORCHESTRATOR_URL", "http://mongodb-orchestrator-service:8000")
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api-service:8084")
SERVICE_NAME = "access-control"

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    service_name: str
    group_name: str
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    group_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class GroupCreate(BaseModel):
    name: str
    description: str
    service_name: str
    permissions: List[str] = []
    parent_group: Optional[str] = None

class GroupUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    parent_group: Optional[str] = None

class ServiceTile(BaseModel):
    service_name: str
    display_name: str
    description: str
    icon: str
    url: str
    enabled: bool = True
    permissions: List[str] = []

class LandingPageData(BaseModel):
    user: Dict[str, Any]
    groups: List[Dict[str, Any]]
    tiles: List[ServiceTile]
    timestamp: datetime

# MongoDB Operations Helper
class MongoDBHelper:
    def __init__(self):
        self.base_url = MONGODB_ORCHESTRATOR_URL
        self.service_name = SERVICE_NAME
    
    async def _make_request(self, operation: str, collection: str, **kwargs):
        """Make request to MongoDB Orchestrator"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/mongodb/operation",
                    headers={"Authorization": f"Bearer {kwargs.get('token', '')}"},
                    json={
                        "service_name": self.service_name,
                        "database_name": "access_control",
                        "collection_name": collection,
                        "operation": operation,
                        **kwargs
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"MongoDB operation failed: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="MongoDB operation failed")
                    
        except httpx.RequestError as e:
            logger.error(f"MongoDB orchestrator connection error: {e}")
            raise HTTPException(status_code=503, detail="MongoDB service unavailable")
    
    async def create_user(self, user_data: dict, token: str):
        """Create a new user"""
        return await self._make_request("insert", "users", data=user_data, token=token)
    
    async def find_user(self, query: dict, token: str):
        """Find user by query"""
        return await self._make_request("find_one", "users", query=query, token=token)
    
    async def find_users(self, query: dict, token: str):
        """Find users by query"""
        return await self._make_request("find", "users", query=query, token=token)
    
    async def update_user(self, query: dict, update: dict, token: str):
        """Update user"""
        return await self._make_request("update", "users", query=query, update=update, token=token)
    
    async def create_group(self, group_data: dict, token: str):
        """Create a new group"""
        return await self._make_request("insert", "groups", data=group_data, token=token)
    
    async def find_group(self, query: dict, token: str):
        """Find group by query"""
        return await self._make_request("find_one", "groups", query=query, token=token)
    
    async def find_groups(self, query: dict, token: str):
        """Find groups by query"""
        return await self._make_request("find", "groups", query=query, token=token)
    
    async def update_group(self, query: dict, update: dict, token: str):
        """Update group"""
        return await self._make_request("update", "groups", query=query, update=update, token=token)

# Auth API Helper
class AuthAPIHelper:
    def __init__(self):
        self.base_url = AUTH_API_URL
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token with Auth API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/auth/validate-token",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(status_code=401, detail="Invalid token")
                    
        except httpx.RequestError as e:
            logger.error(f"Auth API connection error: {e}")
            raise HTTPException(status_code=503, detail="Auth service unavailable")

# Global helpers
mongodb_helper = MongoDBHelper()
auth_helper = AuthAPIHelper()

# Authentication dependency
async def get_current_user(token: str = Depends(httpx.Header("Authorization"))):
    """Get current user from token"""
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token_value = token.split(" ")[1]
    return await auth_helper.validate_token(token_value)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "access-control",
        "timestamp": datetime.utcnow(),
        "dependencies": {
            "mongodb_orchestrator": "connected",
            "auth_api": "connected"
        }
    }

# User Management Endpoints
@app.post("/api/users", status_code=201)
async def create_user(user: UserCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new user"""
    try:
        # Check if user has permission to create users
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if user already exists
        existing_user = await mongodb_helper.find_user(
            {"username": user.username}, 
            current_user.get("access_token", "")
        )
        
        if existing_user.get("data"):
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Create user document
        user_data = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "service_name": user.service_name,
            "group_name": user.group_name,
            "role": user.role,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("username"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await mongodb_helper.create_user(user_data, current_user.get("access_token", ""))
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": result.get("data", {}).get("inserted_id"),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{username}")
async def get_user(username: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user by username"""
    try:
        # Check permissions
        if current_user.get("username") != username and "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        user = await mongodb_helper.find_user(
            {"username": username}, 
            current_user.get("access_token", "")
        )
        
        if not user.get("data"):
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": user.get("data"),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{username}")
async def update_user(username: str, user_update: UserUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update user"""
    try:
        # Check permissions
        if current_user.get("username") != username and "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if user_update.email:
            update_data["email"] = user_update.email
        if user_update.full_name:
            update_data["full_name"] = user_update.full_name
        if user_update.group_name:
            update_data["group_name"] = user_update.group_name
        if user_update.role:
            update_data["role"] = user_update.role
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        result = await mongodb_helper.update_user(
            {"username": username},
            {"$set": update_data},
            current_user.get("access_token", "")
        )
        
        return {
            "success": True,
            "message": "User updated successfully",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Group Management Endpoints
@app.post("/api/groups", status_code=201)
async def create_group(group: GroupCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new group"""
    try:
        # Check if user has permission to create groups
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if group already exists
        existing_group = await mongodb_helper.find_group(
            {"name": group.name, "service_name": group.service_name}, 
            current_user.get("access_token", "")
        )
        
        if existing_group.get("data"):
            raise HTTPException(status_code=409, detail="Group already exists")
        
        # Create group document
        group_data = {
            "name": group.name,
            "description": group.description,
            "service_name": group.service_name,
            "permissions": group.permissions,
            "parent_group": group.parent_group,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("username"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await mongodb_helper.create_group(group_data, current_user.get("access_token", ""))
        
        return {
            "success": True,
            "message": "Group created successfully",
            "group_id": result.get("data", {}).get("inserted_id"),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/groups")
async def get_groups(service_name: Optional[str] = None, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get groups"""
    try:
        query = {"is_active": True}
        if service_name:
            query["service_name"] = service_name
        
        groups = await mongodb_helper.find_groups(query, current_user.get("access_token", ""))
        
        return {
            "success": True,
            "data": groups.get("data", []),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Landing Page Endpoints
@app.get("/api/landing-page")
async def get_landing_page_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get landing page data with user groups and service tiles"""
    try:
        # Get user's groups
        user_groups = await mongodb_helper.find_users(
            {"username": current_user.get("username")}, 
            current_user.get("access_token", "")
        )
        
        user_data = user_groups.get("data", [{}])[0] if user_groups.get("data") else {}
        
        # Get groups for the user
        groups = []
        if user_data.get("group_name"):
            group_data = await mongodb_helper.find_group(
                {"name": user_data["group_name"]}, 
                current_user.get("access_token", "")
            )
            if group_data.get("data"):
                groups.append(group_data["data"])
        
        # Define service tiles based on user's groups and permissions
        tiles = []
        
        # Platform Admin tiles
        if "platform-admin" in current_user.get("roles", []):
            tiles.extend([
                ServiceTile(
                    service_name="admin-dashboard",
                    display_name="Admin Dashboard",
                    description="Platform administration and monitoring",
                    icon="📊",
                    url="http://admin-dashboard-service:80",
                    permissions=["platform-admin"]
                ),
                ServiceTile(
                    service_name="grafana",
                    display_name="Grafana",
                    description="Monitoring dashboards",
                    icon="📈",
                    url="http://prometheus-grafana.observability:80",
                    permissions=["platform-admin", "monitoring-admin"]
                ),
                ServiceTile(
                    service_name="prometheus",
                    display_name="Prometheus",
                    description="Metrics and alerting",
                    icon="📊",
                    url="http://prometheus-kube-prometheus-prometheus.observability:9090",
                    permissions=["platform-admin", "monitoring-admin"]
                ),
                ServiceTile(
                    service_name="keycloak",
                    display_name="Keycloak",
                    description="Identity and access management",
                    icon="🔐",
                    url="http://keycloak:8080",
                    permissions=["platform-admin", "security-admin"]
                )
            ])
        
        # Service-specific tiles based on user's group
        if user_data.get("service_name"):
            service_tiles = {
                "user-service": ServiceTile(
                    service_name="user-service",
                    display_name="User Service",
                    description="User management and profiles",
                    icon="👥",
                    url="http://user-service:8080",
                    permissions=["user-service-admin", "user-service-user"]
                ),
                "order-service": ServiceTile(
                    service_name="order-service",
                    display_name="Order Service",
                    description="Order management and processing",
                    icon="📦",
                    url="http://order-service:8080",
                    permissions=["order-service-admin", "order-service-user"]
                ),
                "inventory-service": ServiceTile(
                    service_name="inventory-service",
                    display_name="Inventory Service",
                    description="Inventory management and tracking",
                    icon="📋",
                    url="http://inventory-service:8080",
                    permissions=["inventory-service-admin", "inventory-service-user"]
                )
            }
            
            if user_data["service_name"] in service_tiles:
                tiles.append(service_tiles[user_data["service_name"]])
        
        return LandingPageData(
            user=user_data,
            groups=groups,
            tiles=tiles,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get landing page data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Service Registration Endpoint
@app.post("/api/services/register")
async def register_service(service_data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Register a new service for access control"""
    try:
        # Check if user has permission to register services
        if "platform-admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Create service document
        service_doc = {
            "name": service_data["name"],
            "display_name": service_data.get("display_name", service_data["name"]),
            "description": service_data.get("description", ""),
            "icon": service_data.get("icon", "🔧"),
            "url": service_data["url"],
            "permissions": service_data.get("permissions", []),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("username"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await mongodb_helper._make_request(
            "insert", "services", 
            data=service_doc, 
            token=current_user.get("access_token", "")
        )
        
        return {
            "success": True,
            "message": "Service registered successfully",
            "service_id": result.get("data", {}).get("inserted_id"),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to register service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
