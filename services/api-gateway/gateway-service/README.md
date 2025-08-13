# API Gateway Service

## 🎯 **Overview**

The API Gateway is the **single entry point** for all external clients to access Nexus Platform services. It provides:

- **Authentication**: Validates JWT tokens from Keycloak
- **Authorization**: Routes requests to appropriate services
- **Security**: IP restrictions, rate limiting, CORS
- **Load Balancing**: Distributes requests across services
- **Monitoring**: Request logging and metrics

## 🏗️ **Architecture**

```
┌─────────────────┐
│   External      │
│   Clients       │
│   (Web, Mobile) │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   API Gateway   │
│   (Port 8080)   │
│                 │
│  • Auth Check   │
│  • Rate Limit   │
│  • CORS         │
│  • Routing      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Internal      │    │   Access        │    │   Other         │
│   Services      │    │   Control       │    │   Services      │
│                 │    │   Service       │    │                 │
│  • Keycloak     │    │   (Port 8083)   │    │  • Admin        │
│  • Landing      │    │                 │    │    Dashboard    │
│    Page         │    │                 │    │  • ID Service   │
│  • Admin        │    │                 │    │  • Parking      │
│    Interface    │    │                 │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Key Features**

### **Security:**
- **JWT Validation**: Validates tokens from Keycloak
- **IP Restrictions**: Limit access to specific IP ranges
- **Rate Limiting**: Prevent abuse
- **CORS Management**: Handle cross-origin requests

### **Routing:**
- **Service Discovery**: Route to appropriate internal services
- **Load Balancing**: Distribute load across service instances
- **Health Checks**: Monitor service availability

### **Monitoring:**
- **Request Logging**: Log all incoming requests
- **Metrics**: Track performance and usage
- **Error Handling**: Graceful error responses

## 🚀 **Quick Start**

### **1. Start the Gateway**
```bash
cd services/api-gateway/gateway-service
python3 gateway_server.py
```

### **2. Test External Access**
```bash
# External clients access through gateway
curl http://localhost:8080/api/health
curl http://localhost:8080/api/services
```

### **3. Internal Services**
```bash
# Internal services remain accessible directly
curl http://localhost:8083/api/health  # Access Control Service
curl http://localhost:8080/realms/nexus-platform  # Keycloak
```

## 📊 **Routing Rules**

| External Path | Internal Service | Purpose |
|---------------|------------------|---------|
| `/api/*` | Access Control Service | Service management |
| `/auth/*` | Keycloak | Authentication |
| `/admin/*` | Admin Dashboard | Platform management |
| `/landing` | Landing Page | User portal |
| `/health` | All Services | Health checks |

## 🔒 **Security Configuration**

### **IP Restrictions:**
```yaml
allowed_ips:
  - "10.0.0.0/8"    # Internal network
  - "172.16.0.0/12" # Docker network
  - "192.168.0.0/16" # Local network
```

### **Rate Limiting:**
```yaml
rate_limits:
  default: "100/minute"
  auth: "10/minute"
  admin: "1000/minute"
```

### **CORS:**
```yaml
cors:
  allowed_origins:
    - "https://platform.nexus.com"
    - "https://admin.nexus.com"
  allowed_methods: ["GET", "POST", "PUT", "DELETE"]
```

## 🔄 **Integration Flow**

### **1. External Client Request:**
```
Client → API Gateway (8080) → Internal Service
```

### **2. Authentication Flow:**
```
1. Client requests /api/services
2. Gateway checks JWT token
3. Gateway validates token with Keycloak
4. Gateway routes to Access Control Service
5. Access Control Service returns data
6. Gateway returns response to client
```

### **3. Internal Service Communication:**
```
API Gateway → Access Control Service (8083)
API Gateway → Keycloak (8080)
API Gateway → Admin Dashboard (8081)
```

## 📈 **Benefits**

### **For Security:**
- Single point of control for external access
- IP restrictions and rate limiting
- Centralized authentication
- No direct exposure of internal services

### **For Scalability:**
- Load balancing across service instances
- Service discovery and health checks
- Easy to add new services
- Independent scaling of gateway and services

### **For Maintenance:**
- Centralized logging and monitoring
- Easy to update routing rules
- Graceful error handling
- Health check aggregation

## 🔮 **Future Enhancements**

1. **Service Mesh**: Istio integration for advanced routing
2. **API Versioning**: Support multiple API versions
3. **Circuit Breakers**: Handle service failures gracefully
4. **Caching**: Redis integration for performance
5. **Analytics**: Request analytics and insights
