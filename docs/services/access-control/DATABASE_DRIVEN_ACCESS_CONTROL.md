# Database-Driven Access Control System

## 🎯 **Overview**

The Nexus Platform now uses a **database-driven access control system** instead of hardcoded group names. This provides:

- **Scalability**: Add new services and groups without code changes
- **Flexibility**: Dynamic access control configuration
- **Maintainability**: Centralized management through database
- **Extensibility**: Easy to add new access levels and permissions

## 🏗️ **Architecture**

### **Database Schema**

```sql
-- Services table
services (
    id, service_id, title, description, icon, url, status
)

-- Groups table (Keycloak groups)
groups (
    id, group_name, group_path, description, is_active
)

-- Service-Group mappings table
service_group_mappings (
    id, service_id, group_id, access_level
)
```

### **API Endpoints**

- `GET /api/health` - Health check
- `GET /api/services` - List all services
- `GET /api/user-access?groups=group1,group2` - Get user accessible services

## 🔧 **Setup Instructions**

### **1. Start the API Server**
```bash
cd services/core/keycloak-service
python3 api_server.py
```

### **2. Access Admin Interface**
```
http://localhost:8082/admin_interface.html
```

### **3. Test the Landing Page**
```
http://localhost:8082/login.html
```

## 📊 **Database Management**

### **Adding a New Service**

1. **Via Database:**
```sql
INSERT INTO services (service_id, title, description, icon, url, status) 
VALUES ('new-service', 'New Service', 'Description', '🔧', 'http://localhost:8085', 'available');
```

2. **Via Admin Interface** (coming soon)

### **Adding a New Group**

1. **Via Database:**
```sql
INSERT INTO groups (group_name, group_path, description) 
VALUES ('new-group', 'nexus/new-group', 'New group description');
```

2. **Via Keycloak Admin Console** (recommended)

### **Creating Access Mappings**

```sql
INSERT INTO service_group_mappings (service_id, group_id, access_level) 
SELECT s.id, g.id, 'read'
FROM services s, groups g
WHERE s.service_id = 'new-service' 
AND g.group_path = 'nexus/new-group';
```

## 🎯 **Access Levels**

- **read**: Basic access to view/use the service
- **write**: Can modify data within the service
- **admin**: Full administrative access

## 🔄 **Migration from Hardcoded Groups**

### **Before (Hardcoded):**
```javascript
const products = [
    {
        id: 'admin-dashboard',
        requiredGroups: ['platform-admin', 'admin-dashboard', 'nexus'],
        // ... other properties
    }
];
```

### **After (Database-Driven):**
```javascript
// Products loaded from API
const products = await fetch('/api/services').then(r => r.json());

// Access control via API
const accessibleServices = await fetch(`/api/user-access?groups=${userGroups.join(',')}`).then(r => r.json());
```

## 🧪 **Testing**

### **Test Different User Groups:**

1. **Platform Admin:**
   ```
   http://localhost:8083/api/user-access?groups=nexus,platform-admin
   ```

2. **Test Client:**
   ```
   http://localhost:8083/api/user-access?groups=test-client,test-client/id-service
   ```

3. **Service Admin:**
   ```
   http://localhost:8083/api/user-access?groups=nexus,service-admin
   ```

### **Expected Results:**

- **Platform Admin**: Access to all services
- **Test Client**: Access only to ID Service and Parking Service
- **Service Admin**: Access to monitoring, logs, and metrics

## 🔒 **Security Considerations**

1. **Database Security**: Use proper authentication for database access
2. **API Security**: Implement rate limiting and authentication
3. **Input Validation**: Validate group names and service IDs
4. **Audit Logging**: Log access control decisions

## 🚀 **Production Deployment**

### **1. Database Migration**
- Use PostgreSQL or MySQL for production
- Implement proper backup strategies
- Set up database replication if needed

### **2. API Server**
- Deploy as a Kubernetes service
- Implement proper monitoring and logging
- Add authentication and authorization

### **3. Configuration Management**
- Use environment variables for database connections
- Implement configuration validation
- Set up proper error handling

## 📈 **Benefits**

### **For Developers:**
- No code changes needed for new services
- Centralized access control logic
- Easy testing and debugging

### **For Administrators:**
- Dynamic service management
- Real-time access control updates
- Comprehensive audit trail

### **For Users:**
- Consistent access control across services
- Transparent permission management
- Better user experience

## 🔮 **Future Enhancements**

1. **Web-based Admin Interface**: Full CRUD operations for services and mappings
2. **Role-based Access Control**: More granular permissions
3. **Audit Logging**: Track all access control decisions
4. **Integration with Keycloak**: Automatic group synchronization
5. **API Authentication**: Secure API endpoints
6. **Caching**: Improve performance with Redis caching
