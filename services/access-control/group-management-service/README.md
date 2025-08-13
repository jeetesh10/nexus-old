# Access Control Service

## 🎯 **Overview**

The Access Control Service is a **separate, independent service** that manages service-to-group mappings and access control logic. It's completely decoupled from Keycloak and can be used with any authentication provider.

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   External      │    │   Access Control │    │   Keycloak      │
│   Clients       │───▶│   Service        │───▶│   (Internal)    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Database       │
                       │   (Services,     │
                       │    Groups,       │
                       │    Mappings)     │
                       └──────────────────┘
```

## 🔧 **Key Features**

- **Authentication Provider Agnostic**: Works with Keycloak, Auth0, or any OIDC provider
- **Database-Driven**: All access control logic stored in database
- **RESTful API**: Clean API for service and group management
- **Scalable**: Easy to add new services and groups
- **Secure**: Internal-only access, exposed through API Gateway

## 🚀 **Quick Start**

### **1. Start the Service**
```bash
cd services/access-control/group-management-service
python3 api_server.py
```

### **2. Test the API**
```bash
curl http://localhost:8083/api/health
curl http://localhost:8083/api/services
```

### **3. Access Admin Interface**
```
http://localhost:8082/admin_interface.html
```

## 📊 **API Endpoints**

- `GET /api/health` - Health check
- `GET /api/services` - List all services
- `GET /api/user-access?groups=group1,group2` - Get user accessible services
- `POST /api/services` - Add new service (admin only)
- `POST /api/mappings` - Create service-group mapping (admin only)

## 🔒 **Security**

- **Internal Access Only**: Service not exposed to external clients
- **API Gateway Integration**: All external requests go through API Gateway
- **Authentication Required**: All admin operations require authentication
- **Audit Logging**: All access control decisions are logged

## 🔄 **Integration with Keycloak**

The service receives user groups from Keycloak but doesn't directly communicate with it:

1. **User logs in** via Keycloak
2. **Keycloak returns** user groups in JWT token
3. **Frontend extracts** groups from token
4. **Frontend calls** Access Control Service with groups
5. **Service returns** accessible services based on database mappings

## 📈 **Benefits of Separation**

### **For Security:**
- Keycloak not exposed to external clients
- Single point of control through API Gateway
- IP restrictions possible on internal services

### **For Flexibility:**
- Can replace Keycloak without affecting access control logic
- Can use different auth providers for different clients
- Independent scaling of auth and access control

### **For Maintenance:**
- Clear separation of concerns
- Independent deployment and updates
- Easier debugging and monitoring
