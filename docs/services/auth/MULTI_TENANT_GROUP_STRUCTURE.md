# Multi-Tenant Group Structure - Keycloak Implementation

## 🏗️ **Architecture Overview**

This document describes the hierarchical group structure implemented in Keycloak to support a multi-tenant, multi-app system where users can have different access levels across different clients and services.

## 🎯 **Group Hierarchy Design**

### **1. Internal Nexus Groups (Platform Management)**
```
nexus (Parent Group)
├── platform-admin
│   ├── Full access to all services
│   ├── System administration capabilities
│   └── User: admin
├── service-admin
│   ├── Access to monitoring and operational services
│   ├── Grafana, Prometheus, Loki access
│   └── Limited administrative access
└── admin-dashnboard
    ├── Access to admin dashboard only
    └── Service management capabilities
```

### **2. Client/Tenant Groups (Multi-Tenant Access)**
```
test-client (Parent Group for Client/Tenant)
├── id-service
│   ├── Access to Identity Resolution Service
│   └── User: test-user
└── parking-service
    ├── Access to Parking Management Service
    └── User: test-user
```

## 🔐 **Access Control Matrix**

### **User Types and Access Levels:**

| User Type | Group Membership | Access Level | Available Services |
|-----------|------------------|--------------|-------------------|
| **Platform Admin** | `nexus/platform-admin` | Full Access | All services |
| **Service Admin** | `nexus/service-admin` | Operational | Monitoring, Logs, Metrics |
| **Dashboard Admin** | `nexus/admin-dashnboard` | Dashboard Only | Admin Dashboard |
| **Client User** | `test-client/id-service` | Service Specific | ID Service only |
| **Client User** | `test-client/parking-service` | Service Specific | Parking Service only |
| **Multi-Service Client** | `test-client/*` | Multi-Service | ID + Parking Services |

## 🚀 **Benefits of This Structure**

### **1. Multi-Tenant Support**
- **Client Isolation**: Each client has their own group hierarchy
- **Service Granularity**: Clients can access specific services only
- **Scalability**: Easy to add new clients and services

### **2. Flexible Access Control**
- **Hierarchical Permissions**: Parent groups inherit to child groups
- **Cross-Client Access**: Users can belong to multiple client groups
- **Service-Level Control**: Fine-grained access to individual services

### **3. Operational Efficiency**
- **Internal vs External**: Clear separation between platform users and client users
- **Role-Based Access**: Different access levels for different user types
- **Audit Trail**: Clear group membership for compliance

## 🔧 **Implementation Details**

### **Group Creation Process:**
1. **Create Parent Group**: `test-client`
2. **Create Service Subgroups**: `id-service`, `parking-service`
3. **Assign Users**: Add users to appropriate subgroups
4. **Configure Access**: Set up service-specific permissions

### **User Assignment Examples:**
```
admin → nexus/platform-admin (Full access)
test-user → test-client/id-service + test-client/parking-service
new-client-user → new-client/selected-services
```

## 📋 **Service Access Mapping**

### **Available Services:**
| Service | Internal Access | Client Access | URL |
|---------|----------------|---------------|-----|
| Admin Dashboard | `nexus/admin-dashnboard` | N/A | `http://localhost:8081` |
| ID Service | `nexus/platform-admin` | `*/id-service` | `http://localhost:8083` |
| Parking Service | `nexus/platform-admin` | `*/parking-service` | `http://localhost:8084` |
| Monitoring | `nexus/service-admin` | N/A | `http://localhost:3000` |
| Logs | `nexus/service-admin` | N/A | `http://localhost:3100` |
| Metrics | `nexus/service-admin` | N/A | `http://localhost:9090` |

## 🎯 **Testing Scenarios**

### **Scenario 1: Platform Admin Access**
- **User**: `admin`
- **Groups**: `nexus/platform-admin`
- **Expected Access**: All services available
- **Test**: Login and verify all tiles are clickable

### **Scenario 2: Client User Access**
- **User**: `test-user`
- **Groups**: `test-client/id-service`, `test-client/parking-service`
- **Expected Access**: ID Service and Parking Service only
- **Test**: Login and verify only relevant tiles are available

### **Scenario 3: Service Admin Access**
- **User**: `service-admin`
- **Groups**: `nexus/service-admin`
- **Expected Access**: Monitoring, Logs, Metrics only
- **Test**: Login and verify operational services are available

## 🔄 **Future Enhancements**

### **1. Dynamic Service Discovery**
- Automatically detect available services based on group membership
- Real-time service availability updates

### **2. Advanced Permission System**
- Service-specific roles within client groups
- Time-based access controls
- Conditional access based on user attributes

### **3. Multi-Client User Support**
- Users belonging to multiple client groups
- Cross-client service access
- Client-specific configurations

## 🎉 **Current Status**

### ✅ **Implemented:**
- Hierarchical group structure
- Multi-tenant client groups
- Service-specific access control
- User group assignments
- Landing page integration

### 🚧 **In Progress:**
- Admin dashboard integration
- Service-specific authentication
- Cross-service authorization

### 📋 **Planned:**
- API gateway integration
- Service mesh integration
- Advanced audit logging
- Self-service user management

## 🔗 **Related Documentation**

- [Keycloak Setup Status](./KEYCLOAK_SETUP_STATUS.md)
- [Developer Guide](./keyclock-dev.md)
- [Admin Dashboard Integration](./ADMIN_DASHBOARD_INTEGRATION.md)
