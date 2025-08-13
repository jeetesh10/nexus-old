# Auth API Service

## 🎯 **Overview**

The Auth API Service provides authentication endpoints for other services in the Nexus Platform. It acts as a bridge between internal services and Keycloak, providing a clean API for token validation, user information, and authentication operations.

## 🔧 **Quick Start**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Start the Service**
```bash
python auth_api.py
```

### **3. Test the Service**
```bash
# Health check
curl http://localhost:8084/api/auth/health

# Validate token
curl "http://localhost:8084/api/auth/validate-token?token=YOUR_JWT_TOKEN"

# Get user info
curl "http://localhost:8084/api/auth/user-info?token=YOUR_JWT_TOKEN"
```

## 📡 **API Endpoints**

### **GET Endpoints**

#### **Health Check**
```
GET /api/auth/health
```
Returns service health status and available endpoints.

#### **Token Validation**
```
GET /api/auth/validate-token?token=JWT_TOKEN
```
Validates JWT token and returns token information.

**Response:**
```json
{
  "valid": true,
  "user_id": "user-uuid",
  "username": "john.doe",
  "email": "john@example.com",
  "exp": 1640995200,
  "iat": 1640908800
}
```

#### **User Information**
```
GET /api/auth/user-info?token=JWT_TOKEN
```
Returns detailed user information from token.

**Response:**
```json
{
  "user_id": "user-uuid",
  "username": "john.doe",
  "email": "john@example.com",
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "groups": ["nexus", "platform-admin"],
  "roles": ["admin", "user"]
}
```

#### **User Groups**
```
GET /api/auth/user-groups?token=JWT_TOKEN
```
Returns user groups from token.

**Response:**
```json
{
  "groups": ["nexus", "platform-admin", "admin-dashboard"]
}
```

#### **OpenID Configuration**
```
GET /api/auth/openid-config
```
Returns OpenID Connect configuration from Keycloak.

### **POST Endpoints**

#### **User Login**
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "john.doe",
  "password": "password123"
}
```
Returns access token and refresh token.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

#### **Token Refresh**
```
POST /api/auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
Returns new access token.

#### **User Logout**
```
POST /api/auth/logout
Content-Type: application/json

{
  "token": "refresh_token_here"
}
```
Logs out user and invalidates tokens.

## 🔐 **Security Features**

### **JWT Validation**
- **Algorithm**: RS256 (RSA with SHA-256)
- **Key Source**: Keycloak JWKS endpoint
- **Audience**: nexus-platform
- **Issuer**: Keycloak realm

### **Token Verification**
- **Signature Verification**: Using Keycloak public keys
- **Expiration Check**: Automatic token expiration validation
- **Audience Validation**: Ensures token is for correct audience
- **Issuer Validation**: Verifies token comes from correct Keycloak realm

### **Error Handling**
- **Invalid Token**: 401 Unauthorized
- **Expired Token**: 401 Unauthorized
- **Missing Token**: 400 Bad Request
- **Server Error**: 500 Internal Server Error

## 🔄 **Integration with Other Services**

### **Service-to-Service Authentication**
Other services can use this API to:
1. **Validate tokens** from client requests
2. **Get user information** for authorization
3. **Check user groups** for access control
4. **Refresh tokens** when needed

### **Example Integration**
```python
import requests

# Validate token in your service
def validate_user_token(token):
    response = requests.get(
        f"http://auth-api-service:8084/api/auth/validate-token",
        params={"token": token}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Get user groups for access control
def get_user_groups(token):
    response = requests.get(
        f"http://auth-api-service:8084/api/auth/user-groups",
        params={"token": token}
    )
    
    if response.status_code == 200:
        return response.json()["groups"]
    else:
        return []
```

## 🚀 **Deployment**

### **Docker**
```bash
# Build image
docker build -t auth-api-service .

# Run container
docker run -p 8084:8084 auth-api-service
```

### **Kubernetes**
```bash
# Apply deployment
kubectl apply -f kubernetes/deployment.yaml

# Check status
kubectl get pods -n nexus-platform -l app=auth-api-service
```

## ⚙️ **Configuration**

### **Environment Variables**
- `KEYCLOAK_BASE_URL`: Keycloak server URL (default: http://localhost:8080)
- `KEYCLOAK_REALM`: Keycloak realm name (default: nexus-platform)
- `KEYCLOAK_CLIENT_ID`: Keycloak client ID (default: nexus-platform)
- `KEYCLOAK_CLIENT_SECRET`: Keycloak client secret

### **Port Configuration**
- **Default Port**: 8084
- **Health Check**: `/api/auth/health`
- **API Base Path**: `/api/auth`

## 📊 **Monitoring**

### **Health Check**
The service provides a comprehensive health check endpoint that includes:
- **Service Status**: Running/stopped
- **Keycloak Connection**: Connected/disconnected
- **Available Endpoints**: List of all API endpoints
- **Timestamp**: Current server time

### **Logging**
- **Request Logging**: All incoming requests
- **Error Logging**: Detailed error information
- **Performance Logging**: Response times and metrics

## 🔮 **Future Enhancements**

1. **Rate Limiting**: Prevent abuse of auth endpoints
2. **Caching**: Cache user information and tokens
3. **Metrics**: Prometheus metrics for monitoring
4. **Audit Logging**: Track all authentication events
5. **Multi-Tenant Support**: Support for multiple Keycloak realms
