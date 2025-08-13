# Keycloak Configuration Updates for HTTPS Support

## 🔧 **Required Keycloak Client Updates:**

### **1. Go to Keycloak Admin Console:**
```
http://localhost:8080/admin/
```

### **2. Navigate to the Client:**
- Realm: `nexus-platform`
- Clients → Click on `nexus-landing-page`

### **3. Update Redirect URIs:**
In the **"Settings"** tab, update **"Valid Redirect URIs"** to include:
```
http://localhost:8082/*
https://localhost:8082/*
```

### **4. Update Web Origins:**
In the **"Settings"** tab, update **"Web Origins"** to include:
```
http://localhost:8082
https://localhost:8082
```

### **5. Save Changes:**
Click **"Save"** to apply the changes.

## 🎯 **Why These Changes:**

1. **Development Support:** HTTP URLs for local development
2. **Production Ready:** HTTPS URLs for QA/production environments
3. **Flexible Deployment:** Same configuration works in both environments

## 🧪 **Test After Configuration:**

1. **HTTP Test:** http://localhost:8082/login.html
2. **HTTPS Test:** https://localhost:8082/login.html (when SSL is configured)

## 📝 **Future Production Configuration:**

When deploying to production, you'll need to:

1. **Update Keycloak URLs** in `config.js`
2. **Configure SSL certificates** for all services
3. **Update DNS** to point to your production domains
4. **Configure load balancers** for HTTPS termination

## 🔒 **Security Considerations:**

- **HTTPS Required:** All production environments should use HTTPS
- **Secure Cookies:** Keycloak will automatically use secure cookies in HTTPS
- **CORS Headers:** Ensure proper CORS configuration for production domains
