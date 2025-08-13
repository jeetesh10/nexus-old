# Admin Dashboard Service Documentation

## 📚 **Available Documentation**

### **Features & Enhancements**
- **[Enhanced Dashboard](ENHANCED_DASHBOARD.md)** - Dashboard features and capabilities
- **[Role-Based Access Control](ROLE_BASED_ACCESS.md)** - RBAC system implementation
- **[Port Configuration](PORT_CHANGE.md)** - Port management and configuration

## 🎯 **Service Overview**

The Admin Dashboard Service provides:
- **Unified Platform Management**: Single interface for all platform administration
- **Role-Based Access**: Granular permissions for different user types
- **Service Management**: Start, stop, and monitor platform services
- **Embedded Tools**: Integrated monitoring and logging tools

## 🔧 **Quick Start**

### **1. Start the Service**
```bash
cd services/admin-dashboard-service
python3 src/main.py
```

### **2. Access the Dashboard**
```
http://localhost:8081
```

### **3. Default Credentials**
- **Username**: admin
- **Password**: AdminPass123

## 📊 **Architecture**

```
┌─────────────────┐
│   Admin Users   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   API Gateway   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Admin         │
│   Dashboard     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Platform      │
│   Services      │
└─────────────────┘
```

## 🔐 **Role-Based Access**

### **Available Roles**
- **platform-admin**: Full platform access
- **service-admin**: Service management only
- **monitoring-admin**: Monitoring tools access
- **security-admin**: Security and authentication
- **developer**: Development and testing tools

### **Access Matrix**
| Role | Dashboard | Services | Monitoring | Security | Developer |
|------|-----------|----------|------------|----------|-----------|
| platform-admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| service-admin | ✅ | ✅ | ❌ | ❌ | ❌ |
| monitoring-admin | ✅ | ❌ | ✅ | ❌ | ❌ |
| security-admin | ✅ | ❌ | ❌ | ✅ | ❌ |
| developer | ✅ | ❌ | ❌ | ❌ | ✅ |

## 🔄 **Integration**

The Admin Dashboard integrates with:
- **API Gateway**: For external access
- **Access Control Service**: For permission management
- **Monitoring Stack**: Prometheus, Grafana, Loki
- **Kubernetes**: For service orchestration

## 📈 **Features**

### **Service Management**
- Start/stop platform services
- View service status and health
- Monitor resource usage
- View service logs

### **Monitoring Integration**
- Embedded Grafana dashboards
- Real-time metrics from Prometheus
- Centralized logging with Loki
- Alert management with Alertmanager

### **User Management**
- Role-based access control
- User profile management
- Session management
- Audit logging

## 🔮 **Future Enhancements**

1. **Advanced Analytics**: Service performance insights
2. **Automated Scaling**: Auto-scaling based on metrics
3. **Configuration Management**: Centralized service configuration
4. **Backup & Recovery**: Automated backup management
5. **Multi-Environment Support**: Dev, staging, production
