# Auth API Service

**Purpose**: JWT validation and group-based authorization for Nexus Platform

## 🎯 **Core Responsibilities**

1. **JWT Validation**: Validate tokens issued by Keycloak
2. **Group Parsing**: Extract permissions from Keycloak groups
3. **Authorization**: Make access decisions based on groups
4. **No Authentication**: Users authenticate directly with Keycloak

## 🏗️ **Architecture**

```
User → Keycloak (Direct) → JWT Token → Auth API (Validate + Authorize)
```

### **Key Design Principles:**
- ✅ **Stateless**: No database, pure JWT processing
- ✅ **Fast**: In-memory group parsing and caching
- ✅ **Secure**: RSA signature validation with Keycloak public keys
- ✅ **Simple**: Single responsibility - authorization only

## 📋 **API Endpoints**

### **Core Authorization**
```http
POST /api/auth/validate
{
  "jwt_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "resource": "id-service",
  "client_context": "acmy",
  "action": "read"
}
```

**Response:**
```json
{
  "valid": true,
  "allowed": true,
  "permissions": {
    "role": "customer",
    "subscription": "pro+",
    "features": ["bulk-operations", "webhooks"]
  },
  "user_context": {
    "email": "john@acmy.com",
    "client": "acmy"
  },
  "expires_at": "2025-08-16T12:00:00Z"
}
```

### **Convenience Endpoints**
```http
GET /api/auth/user-permissions?token=JWT_TOKEN    # Get all user permissions
GET /api/auth/health                              # Health check
```

## 🔐 **Group-Based Authorization**

### **Group Hierarchy Format:**
```
{Client}/{Service}/Role/{Role}
{Client}/{Service}/Subscription/{Level}

Examples:
- Acmy/ID services/Role/Customer
- Acmy/ID services/Subscription/Pro+
- Nexus/Employee/Admin
```

### **Authorization Logic:**
```javascript
// For request: "Can user access ID service for Acmy?"
const userGroups = ["Acmy/ID services/Role/Customer", "Acmy/ID services/Subscription/Pro+"];
const permissions = parseGroups(userGroups, "acmy", "id-service");
// Returns: { role: "customer", subscription: "pro+", allowed: true }
```

## 🚀 **Quick Start**

### **Development**
```bash
cd services/auth-api-service
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python src/main.py
```

### **Test with Keycloak Token**
```bash
# Get token from Keycloak
curl -X POST "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=nexus-platform&username=test-user&password=TestPass123"

# Validate with Auth API
curl -X POST "http://localhost:8085/api/auth/validate" \
  -H "Content-Type: application/json" \
  -d '{"jwt_token": "YOUR_JWT_TOKEN", "resource": "id-service", "client_context": "nexus", "action": "read"}'
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
KEYCLOAK_BASE_URL=http://localhost:8080
KEYCLOAK_REALM=nexus-platform
SERVICE_PORT=8085
LOG_LEVEL=INFO
```

### **Keycloak Integration**
- **JWKS URL**: `{KEYCLOAK_BASE_URL}/realms/{REALM}/protocol/openid-connect/certs`
- **Token Validation**: RS256 signature verification
- **Group Claims**: Extracted from `groups` claim in JWT

## 🧪 **Testing**

### **Unit Tests**
```bash
python -m pytest tests/unit/
```

### **Integration Tests**
```bash
# Requires running Keycloak
python -m pytest tests/integration/
```

### **Manual Testing**
```bash
# Health check
curl http://localhost:8085/api/auth/health

# Token validation (requires valid JWT)
curl -X POST http://localhost:8085/api/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"jwt_token": "YOUR_TOKEN", "resource": "test", "action": "read"}'
```

## 📊 **Service Integration**

### **Other Services Usage**
```python
# Example: ID Service using Auth API
import requests

def authorize_request(jwt_token, action):
    response = requests.post("http://auth-api-service:8085/api/auth/validate", json={
        "jwt_token": jwt_token,
        "resource": "id-service", 
        "client_context": request.headers.get("X-Client-Context", "nexus"),
        "action": action
    })
    
    if response.json().get("allowed"):
        return response.json()["permissions"]
    else:
        raise PermissionDenied("Access denied")
```

### **Frontend Integration**
```javascript
// Frontend calls API with JWT from Keycloak
const token = localStorage.getItem('keycloak_token');
const response = await fetch('/api/id-service/lookup', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'X-Client-Context': 'acmy'  // Important for multi-client
    }
});
```

## 🔒 **Security Features**

- **RSA Signature Verification**: Uses Keycloak public keys
- **Token Expiration**: Automatic expiration checking
- **Issuer Validation**: Ensures token from correct Keycloak realm
- **Audience Validation**: Validates token audience claim
- **No Secret Storage**: No credentials stored in service

## 📈 **Performance**

- **Stateless**: No database queries
- **Fast**: In-memory group processing
- **Cacheable**: JWT validation results can be cached
- **Scalable**: Pure computation, horizontal scaling

## 🛠️ **Deployment**

### **Docker**
```bash
docker build -t auth-api-service .
docker run -p 8085:8085 -e KEYCLOAK_BASE_URL=http://keycloak:8080 auth-api-service
```

### **Kubernetes**
```bash
kubectl apply -f kubernetes/
```

## 🔮 **Future Enhancements**

1. **Permission Caching**: Redis cache for frequent authorizations
2. **Rate Limiting**: Protect against abuse
3. **Metrics**: Prometheus metrics for monitoring
4. **Audit Logging**: Optional audit trail
5. **Multi-Realm**: Support multiple Keycloak realms

---

**Status**: ✅ **Ready for Implementation**  
**Tech Stack**: Python + FastAPI + PyJWT + Requests  
**Port**: 8085  
**Dependencies**: Keycloak (for JWT validation)
