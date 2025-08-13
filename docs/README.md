# Nexus Platform Documentation

Welcome to the Nexus Platform documentation! This directory contains comprehensive documentation organized by service and platform level.

## 📁 **Documentation Structure**

```
docs/
├── README.md                    # This file - Documentation index
├── platform/                    # Platform-level documentation
│   ├── ARCHITECTURE_OVERVIEW.md # High-level architecture
│   ├── PROJECT_STRUCTURE.md     # Project organization
│   └── SETUP_GUIDE.md          # Complete setup guide
└── services/                    # Service-specific documentation
    ├── auth/                    # Authentication service
    ├── access-control/          # Access control service
    ├── api-gateway/             # API Gateway service
    ├── admin-dashboard/         # Admin dashboard service
    ├── monitoring/              # Monitoring and observability
    └── frontend/                # Frontend and UI services
```

## 🎯 **Quick Navigation**

### **🚀 Getting Started**
1. **[Setup Guide](platform/SETUP_GUIDE.md)** - Complete platform setup
2. **[Architecture Overview](platform/ARCHITECTURE_OVERVIEW.md)** - Understand the platform
3. **[Project Structure](platform/PROJECT_STRUCTURE.md)** - Navigate the codebase
4. **[Production Requirements](platform/PRODUCTION_REQUIREMENTS.md)** - Production NFRs and requirements
5. **[Implementation Plan](platform/IMPLEMENTATION_PLAN.md)** - Detailed APISIX + Linkerd migration plan
6. **[Architecture Decisions](platform/ARCHITECTURE_DECISIONS.md)** - Why APISIX + Linkerd was chosen
7. **[API Gateway vs Service Mesh](platform/API_GATEWAY_VS_SERVICE_MESH.md)** - Performance comparison and analysis
8. **[API Documentation Standards](platform/API_DOCUMENTATION_STANDARDS.md)** - OpenAPI/Swagger and Postman standards

### **🔧 Service Documentation**

#### **Authentication Service** ([docs/services/auth/](services/auth/))
- **[README](services/auth/README.md)** - Service overview and quick start
- **[Keycloak Development Guide](services/auth/keyclock-dev.md)** - Complete Keycloak setup
- **[Setup Status](services/auth/KEYCLOAK_SETUP_STATUS.md)** - Current status and troubleshooting
- **[Multi-Tenant Groups](services/auth/MULTI_TENANT_GROUP_STRUCTURE.md)** - Group hierarchy
- **[API Test Cases](services/auth/API_TEST_CASES.md)** - Comprehensive test cases and validation

#### **Access Control Service** ([docs/services/access-control/](services/access-control/))
- **[README](services/access-control/README.md)** - Service overview and quick start
- **[Database-Driven Access Control](services/access-control/DATABASE_DRIVEN_ACCESS_CONTROL.md)** - Implementation details

#### **API Gateway** ([docs/services/api-gateway/](services/api-gateway/))
- **[README](services/api-gateway/README.md)** - Gateway configuration and routing

#### **Admin Dashboard** ([docs/services/admin-dashboard/](services/admin-dashboard/))
- **[README](services/admin-dashboard/README.md)** - Service overview and features
- **[Enhanced Dashboard](services/admin-dashboard/ENHANCED_DASHBOARD.md)** - Dashboard capabilities
- **[Role-Based Access](services/admin-dashboard/ROLE_BASED_ACCESS.md)** - RBAC implementation
- **[Port Configuration](services/admin-dashboard/PORT_CHANGE.md)** - Port management

#### **Monitoring Service** ([docs/services/monitoring/](services/monitoring/))
- **[README](services/monitoring/README.md)** - Service overview and setup
- **[Prometheus Review](services/monitoring/PROMETHEUS_REVIEW_COMPLETE.md)** - Metrics and monitoring
- **[Real Data Guide](services/monitoring/REAL_DATA_GUIDE.md)** - Configure real monitoring data

#### **Frontend Service** ([docs/services/frontend/](services/frontend/))
- **[README](services/frontend/README.md)** - Service overview and UI components
- **[Button Decision](services/frontend/BUTTON_DECISION.md)** - UI design decisions
- **[Embedded Experience](services/frontend/EMBEDDED_EXPERIENCE_EXPLAINED.md)** - Tool integration

## 🎯 **Documentation by Use Case**

### **For Platform Administrators**
1. **[Setup Guide](platform/SETUP_GUIDE.md)** - Initial platform setup
2. **[Admin Dashboard](services/admin-dashboard/README.md)** - Platform administration
3. **[Monitoring Service](services/monitoring/README.md)** - System monitoring
4. **[Architecture Overview](platform/ARCHITECTURE_OVERVIEW.md)** - Platform understanding

### **For Developers**
1. **[Project Structure](platform/PROJECT_STRUCTURE.md)** - Codebase navigation
2. **[Authentication Service](services/auth/README.md)** - Auth implementation
3. **[Access Control Service](services/access-control/README.md)** - Permission system
4. **[API Gateway](services/api-gateway/README.md)** - Service integration

### **For DevOps Engineers**
1. **[Setup Guide](platform/SETUP_GUIDE.md)** - Deployment instructions
2. **[Production Requirements](platform/PRODUCTION_REQUIREMENTS.md)** - Production standards and NFRs
3. **[Implementation Plan](platform/IMPLEMENTATION_PLAN.md)** - APISIX + Linkerd deployment
4. **[Monitoring Service](services/monitoring/README.md)** - Observability setup
5. **[Architecture Overview](platform/ARCHITECTURE_OVERVIEW.md)** - Infrastructure understanding
6. **[Project Structure](platform/PROJECT_STRUCTURE.md)** - Deployment structure

### **For UI/UX Designers**
1. **[Frontend Service](services/frontend/README.md)** - UI components and design
2. **[Button Decision](services/frontend/BUTTON_DECISION.md)** - Design decisions
3. **[Embedded Experience](services/frontend/EMBEDDED_EXPERIENCE_EXPLAINED.md)** - Tool integration

## 🔍 **Finding Documentation**

### **By Service**
- **Authentication**: [services/auth/](services/auth/)
- **Access Control**: [services/access-control/](services/access-control/)
- **API Gateway**: [services/api-gateway/](services/api-gateway/)
- **Admin Dashboard**: [services/admin-dashboard/](services/admin-dashboard/)
- **Monitoring**: [services/monitoring/](services/monitoring/)
- **Frontend**: [services/frontend/](services/frontend/)

### **By Topic**
- **Setup & Configuration**: [platform/SETUP_GUIDE.md](platform/SETUP_GUIDE.md)
- **Production & NFRs**: [platform/PRODUCTION_REQUIREMENTS.md](platform/PRODUCTION_REQUIREMENTS.md)
- **Implementation**: [platform/IMPLEMENTATION_PLAN.md](platform/IMPLEMENTATION_PLAN.md)
- **Architecture**: [platform/ARCHITECTURE_OVERVIEW.md](platform/ARCHITECTURE_OVERVIEW.md)
- **Architecture Decisions**: [platform/ARCHITECTURE_DECISIONS.md](platform/ARCHITECTURE_DECISIONS.md)
- **Performance Analysis**: [platform/API_GATEWAY_VS_SERVICE_MESH.md](platform/API_GATEWAY_VS_SERVICE_MESH.md)
- **API Documentation**: [platform/API_DOCUMENTATION_STANDARDS.md](platform/API_DOCUMENTATION_STANDARDS.md)
- **Project Structure**: [platform/PROJECT_STRUCTURE.md](platform/PROJECT_STRUCTURE.md)
- **Security**: [services/auth/](services/auth/), [services/access-control/](services/access-control/)
- **Testing**: [services/auth/API_TEST_CASES.md](services/auth/API_TEST_CASES.md)
- **Monitoring**: [services/monitoring/](services/monitoring/)
- **UI/UX**: [services/frontend/](services/frontend/)

## 📝 **Contributing to Documentation**

### **Documentation Standards**
1. **Service-Specific**: Each service has its own documentation folder
2. **README Files**: Each service folder has a README.md with overview
3. **Consistent Format**: Use markdown with clear headings and structure
4. **Code Examples**: Include practical code examples and commands
5. **Cross-References**: Link to related documentation

### **Adding New Documentation**
1. **Identify Service**: Place docs in appropriate service folder
2. **Update README**: Add reference to new docs in service README
3. **Update Index**: Add entry to this main README.md
4. **Cross-Reference**: Link to related documentation

## 🔗 **External Resources**

- **[Main Project README](../README.md)** - Project overview and quick start
- **[Scripts](../scripts/)** - Platform startup and management scripts
- **[Services](../services/)** - Service source code and configuration

## 📞 **Getting Help**

If you can't find the documentation you need:
1. **Check the service-specific README** in the appropriate service folder
2. **Review the platform-level documentation** for architectural guidance
3. **Search the codebase** for implementation examples
4. **Create an issue** if documentation is missing or unclear

---

*This documentation is organized to help you quickly find the information you need. Each service has its own documentation folder with a README.md file that provides an overview and links to detailed documentation.*
