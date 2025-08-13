# Role-Based Access Control (RBAC) System

## Overview

The Nexus Admin Dashboard now includes a comprehensive role-based access control system that allows different user roles to access specific platform tools and services. This system is designed to integrate seamlessly with Keycloak for enterprise-grade authentication and authorization.

## 🎯 Design Philosophy

### **Scalable Architecture**
- **Vertical tabs on the right side** - Better for growing number of services
- **Role-based tab visibility** - Users only see what they're authorized to access
- **Modular tab system** - Easy to add new services and roles
- **Future-ready** - Designed for Keycloak integration

### **Single Platform Admin Interface**
- **One URL to rule them all** - All platform management from one place
- **Consistent user experience** - Same interface for all tools
- **Centralized access control** - Manage permissions in one place
- **Scalable design** - Can accommodate unlimited services

## 🔐 Role System

### **Available Roles**

| Role | Description | Access |
|------|-------------|---------|
| `platform-admin` | Full platform access | All tabs and services |
| `service-admin` | Service management | Services tab only |
| `monitoring-admin` | Monitoring tools | Grafana, Prometheus, Loki, Alertmanager |
| `security-admin` | Security tools | Keycloak (when deployed) |
| `developer` | Development tools | API documentation and testing |

### **Tab Access Matrix**

| Tab | platform-admin | service-admin | monitoring-admin | security-admin | developer |
|-----|----------------|---------------|------------------|----------------|-----------|
| 📊 Services | ✅ | ✅ | ❌ | ❌ | ❌ |
| 📈 Grafana | ✅ | ❌ | ✅ | ❌ | ❌ |
| 📊 Prometheus | ✅ | ❌ | ✅ | ❌ | ❌ |
| 📝 Loki | ✅ | ❌ | ✅ | ❌ | ❌ |
| 🚨 Alertmanager | ✅ | ❌ | ✅ | ❌ | ❌ |
| 🔐 Keycloak | ✅ | ❌ | ❌ | ✅ | ❌ |
| 🔧 API | ✅ | ❌ | ❌ | ❌ | ✅ |

## 🏗️ Architecture

### **Current Implementation**
- **Static role assignment** - Currently hardcoded as `platform-admin`
- **Client-side filtering** - Tabs filtered based on user role
- **Configurable tab system** - Easy to add/remove tabs and roles

### **Future Keycloak Integration**
```javascript
// Future implementation
async function getUserRole() {
    // Get user info from Keycloak
    const userInfo = await keycloak.getUserInfo();
    const groups = userInfo.groups || [];
    
    // Map Keycloak groups to dashboard roles
    if (groups.includes('platform-admins')) return 'platform-admin';
    if (groups.includes('monitoring-team')) return 'monitoring-admin';
    if (groups.includes('security-team')) return 'security-admin';
    if (groups.includes('developers')) return 'developer';
    
    return 'service-admin'; // Default role
}
```

## 📋 Tab Configuration

### **Adding New Tabs**
To add a new service tab, update the `TAB_CONFIG` in `main.py`:

```python
TAB_CONFIG = {
    "new-service": {
        "id": "new-service",
        "name": "🆕 New Service",
        "icon": "🆕",
        "roles": ["platform-admin", "service-admin"],
        "description": "Description of the new service",
        "url": "http://localhost:8082",  # Optional
        "enabled": True  # Set to False if service not deployed
    }
}
```

### **Adding New Roles**
1. Update the role matrix above
2. Add role to relevant tabs in `TAB_CONFIG`
3. Update Keycloak group mapping (when integrated)

## 🚀 Usage Examples

### **Platform Administrator**
- **Access**: All tabs and services
- **Use case**: Full platform management
- **Typical users**: DevOps engineers, platform architects

### **Service Administrator**
- **Access**: Services tab only
- **Use case**: Start/stop services, monitor service health
- **Typical users**: Application owners, service managers

### **Monitoring Administrator**
- **Access**: Grafana, Prometheus, Loki, Alertmanager
- **Use case**: Monitor platform health, configure alerts
- **Typical users**: SREs, monitoring specialists

### **Security Administrator**
- **Access**: Keycloak admin console
- **Use case**: Manage users, roles, and authentication
- **Typical users**: Security engineers, identity managers

### **Developer**
- **Access**: API documentation and testing
- **Use case**: Test API endpoints, understand integrations
- **Typical users**: Developers, integration specialists

## 🔧 Implementation Details

### **Current State**
- **Role**: Hardcoded as `platform-admin`
- **Authentication**: None (will be added with Keycloak)
- **Authorization**: Client-side filtering
- **Persistence**: None (will be added with Keycloak)

### **Future Enhancements**
1. **Keycloak Integration**
   - OAuth2/OIDC authentication
   - Group-based role mapping
   - Session management

2. **Advanced Features**
   - Dynamic role assignment
   - Audit logging
   - Permission granularity
   - Multi-tenant support

3. **UI Enhancements**
   - Role switcher
   - Permission indicators
   - Access denied messages
   - User profile management

## 🎨 UI Features

### **Vertical Sidebar**
- **Fixed position** on the right side
- **Smooth animations** and hover effects
- **Responsive design** for mobile devices
- **Role-based visibility** of tabs

### **User Information**
- **Current user display** in top-right corner
- **Role badge** showing current permissions
- **Future**: User avatar and profile menu

### **Tab Features**
- **Icons and descriptions** for each service
- **Disabled state** for unavailable services
- **Hover effects** and visual feedback
- **Active state** indication

## 🔮 Roadmap

### **Phase 1: Current (Complete)**
- ✅ Vertical tab layout
- ✅ Role-based tab filtering
- ✅ Scalable tab system
- ✅ Foundation for Keycloak integration

### **Phase 2: Keycloak Integration**
- 🔄 OAuth2/OIDC authentication
- 🔄 Group-based role mapping
- 🔄 Session management
- 🔄 Logout functionality

### **Phase 3: Advanced Features**
- 📋 Audit logging
- 📋 Permission granularity
- 📋 Multi-tenant support
- 📋 Role management UI

### **Phase 4: Enterprise Features**
- 🏢 SSO integration
- 🏢 Advanced authorization policies
- 🏢 Compliance reporting
- 🏢 Integration with enterprise directories

## 🧪 Testing

### **Role Testing**
```bash
# Test different roles by modifying the JavaScript
# In browser console:
currentUserRole = 'monitoring-admin';
initializeTabs();
```

### **Tab Testing**
```bash
# Test tab functionality
curl http://localhost:8081/api/services
```

### **Integration Testing**
```bash
# Test all services are accessible
./start-dashboard.sh
# Visit http://localhost:8081
```

## 📚 Related Documentation

- [README.md](./README.md) - Main project documentation
- [PORT_CHANGE.md](./PORT_CHANGE.md) - Port configuration details
- [developer guide](./developer%20guide) - Development guidelines

## 🤝 Contributing

When adding new services or roles:

1. **Update `TAB_CONFIG`** with new service details
2. **Update role matrix** in this document
3. **Add tab content** in the HTML template
4. **Test role-based access** for different user types
5. **Update documentation** with new capabilities

This role-based system provides a solid foundation for enterprise-grade platform administration while maintaining simplicity and scalability.
