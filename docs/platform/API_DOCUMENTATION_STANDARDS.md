# API Documentation Standards: Nexus Platform

## 🎯 **Executive Summary**

This document defines the API documentation standards for the Nexus Platform, ensuring consistent, comprehensive, and testable API documentation across all services.

## 📋 **API Documentation Requirements**

### **1. OpenAPI/Swagger Specification**

#### **Mandatory Requirements**
- **OpenAPI 3.0+**: All APIs must use OpenAPI 3.0 specification
- **Auto-Generation**: APIs must auto-generate OpenAPI specs from code
- **Interactive Documentation**: Swagger UI must be available for all APIs
- **Version Control**: API versions must be clearly documented
- **Schema Validation**: All request/response schemas must be validated

#### **Documentation Standards**
- **Complete Coverage**: All endpoints must be documented
- **Request/Response Examples**: Real-world examples for all endpoints
- **Error Responses**: All possible error codes and messages
- **Authentication**: Clear authentication requirements
- **Rate Limiting**: Rate limit information for each endpoint

### **2. Postman Collection Generation**

#### **Automatic Generation**
- **OpenAPI to Postman**: Auto-generate Postman collections from OpenAPI specs
- **Environment Variables**: Separate environments for dev/staging/prod
- **Test Cases**: Pre-written test cases for all endpoints
- **Authentication**: Automatic token handling and refresh
- **Data Validation**: Response validation tests

#### **Collection Structure**
- **Service-Based**: Separate collections per service
- **Environment-Specific**: Different environments for different stages
- **Test Suites**: Organized test suites for different scenarios
- **Documentation**: Inline documentation for each request

### **3. Testing Framework**

#### **Test Case Requirements**
- **Happy Path**: Successful request/response scenarios
- **Error Cases**: All error scenarios and edge cases
- **Authentication**: Token validation and refresh tests
- **Authorization**: Permission and access control tests
- **Performance**: Response time and throughput tests
- **Load Testing**: High-volume request testing

#### **Test Documentation**
- **Step-by-Step**: Clear steps for each test case
- **Expected Results**: Detailed expected outcomes
- **Prerequisites**: Required setup and data
- **Cleanup**: Post-test cleanup procedures

## 🔧 **Implementation Standards**

### **1. OpenAPI Specification Structure**

#### **Base Template**
```yaml
openapi: 3.0.3
info:
  title: Nexus Platform API
  description: Comprehensive API documentation for Nexus Platform
  version: 1.0.0
  contact:
    name: Nexus Platform Team
    email: api@nexus.platform
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.nexus.platform/v1
    description: Production server
  - url: https://staging-api.nexus.platform/v1
    description: Staging server
  - url: http://localhost:8080/v1
    description: Development server

security:
  - bearerAuth: []

paths:
  # API endpoints will be defined here

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token from Keycloak authentication

  schemas:
    # Common schemas will be defined here

  responses:
    # Common responses will be defined here
```

#### **Endpoint Documentation Template**
```yaml
/api/auth/login:
  post:
    tags:
      - Authentication
    summary: User login
    description: Authenticate user and return JWT tokens
    operationId: loginUser
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LoginRequest'
          examples:
            valid_login:
              summary: Valid login credentials
              value:
                username: "john.doe"
                password: "SecurePass123"
            invalid_login:
              summary: Invalid credentials
              value:
                username: "invalid"
                password: "wrong"
    responses:
      '200':
        description: Login successful
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginResponse'
            examples:
              success:
                summary: Successful login response
                value:
                  access_token: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
                  refresh_token: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
                  expires_in: 300
                  token_type: "Bearer"
      '401':
        description: Authentication failed
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
            examples:
              invalid_credentials:
                summary: Invalid credentials error
                value:
                  error: "invalid_credentials"
                  error_description: "Invalid username or password"
                  status_code: 401
```

### **2. Schema Definitions**

#### **Common Request Schemas**
```yaml
components:
  schemas:
    LoginRequest:
      type: object
      required:
        - username
        - password
      properties:
        username:
          type: string
          description: User's username or email
          example: "john.doe"
          minLength: 3
          maxLength: 50
        password:
          type: string
          description: User's password
          example: "SecurePass123"
          minLength: 8
          maxLength: 128
          format: password

    TokenValidationRequest:
      type: object
      required:
        - token
      properties:
        token:
          type: string
          description: JWT token to validate
          example: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

    UserAccessRequest:
      type: object
      required:
        - user_id
        - service_id
      properties:
        user_id:
          type: string
          description: User's unique identifier
          example: "123e4567-e89b-12d3-a456-426614174000"
        service_id:
          type: string
          description: Service identifier
          example: "admin-dashboard"
```

#### **Common Response Schemas**
```yaml
components:
  schemas:
    LoginResponse:
      type: object
      properties:
        access_token:
          type: string
          description: JWT access token
          example: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        refresh_token:
          type: string
          description: JWT refresh token
          example: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        expires_in:
          type: integer
          description: Token expiration time in seconds
          example: 300
        token_type:
          type: string
          description: Token type
          example: "Bearer"

    UserInfoResponse:
      type: object
      properties:
        user_id:
          type: string
          description: User's unique identifier
          example: "123e4567-e89b-12d3-a456-426614174000"
        username:
          type: string
          description: User's username
          example: "john.doe"
        email:
          type: string
          description: User's email address
          example: "john.doe@example.com"
        name:
          type: string
          description: User's full name
          example: "John Doe"
        groups:
          type: array
          description: User's group memberships
          items:
            type: string
          example: ["nexus", "platform-admin"]
        roles:
          type: array
          description: User's roles
          items:
            type: string
          example: ["admin", "user"]

    ServiceAccessResponse:
      type: object
      properties:
        has_access:
          type: boolean
          description: Whether user has access to the service
          example: true
        service_id:
          type: string
          description: Service identifier
          example: "admin-dashboard"
        access_level:
          type: string
          description: Access level granted
          example: "read"
        groups_required:
          type: array
          description: Groups required for access
          items:
            type: string
          example: ["nexus", "platform-admin"]

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Error code
          example: "invalid_credentials"
        error_description:
          type: string
          description: Detailed error message
          example: "Invalid username or password"
        status_code:
          type: integer
          description: HTTP status code
          example: 401
        timestamp:
          type: string
          format: date-time
          description: Error timestamp
          example: "2024-01-15T10:30:00Z"
        request_id:
          type: string
          description: Unique request identifier
          example: "req_123456789"
```

### **3. Common Response Definitions**
```yaml
components:
  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            no_token:
              summary: No authentication token provided
              value:
                error: "unauthorized"
                error_description: "Authentication token required"
                status_code: 401
                timestamp: "2024-01-15T10:30:00Z"
                request_id: "req_123456789"

    Forbidden:
      description: Access denied
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            insufficient_permissions:
              summary: User lacks required permissions
              value:
                error: "forbidden"
                error_description: "Insufficient permissions for this operation"
                status_code: 403
                timestamp: "2024-01-15T10:30:00Z"
                request_id: "req_123456789"

    ValidationError:
      description: Request validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            invalid_input:
              summary: Invalid request parameters
              value:
                error: "validation_error"
                error_description: "Invalid request parameters"
                status_code: 400
                timestamp: "2024-01-15T10:30:00Z"
                request_id: "req_123456789"

    RateLimitExceeded:
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            too_many_requests:
              summary: Rate limit exceeded
              value:
                error: "rate_limit_exceeded"
                error_description: "Too many requests, please try again later"
                status_code: 429
                timestamp: "2024-01-15T10:30:00Z"
                request_id: "req_123456789"

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            server_error:
              summary: Internal server error
              value:
                error: "internal_server_error"
                error_description: "An unexpected error occurred"
                status_code: 500
                timestamp: "2024-01-15T10:30:00Z"
                request_id: "req_123456789"
```

## 🧪 **Testing Framework Standards**

### **1. Test Case Categories**

#### **Authentication Tests**
- **Valid Login**: Successful authentication with valid credentials
- **Invalid Credentials**: Failed authentication with wrong credentials
- **Missing Credentials**: Authentication attempt without credentials
- **Token Validation**: Valid JWT token validation
- **Token Refresh**: Token refresh with valid refresh token
- **Token Expiration**: Expired token handling
- **Invalid Token**: Malformed or invalid token handling

#### **Authorization Tests**
- **Valid Access**: User with proper permissions accessing service
- **Insufficient Permissions**: User without required permissions
- **Group-Based Access**: Access control based on user groups
- **Role-Based Access**: Access control based on user roles
- **Tenant Isolation**: Multi-tenant access control

#### **Functional Tests**
- **Happy Path**: Successful API operations
- **Edge Cases**: Boundary conditions and edge cases
- **Data Validation**: Input validation and sanitization
- **Error Handling**: Proper error responses
- **Rate Limiting**: Rate limit enforcement

#### **Performance Tests**
- **Response Time**: API response time under normal load
- **Throughput**: Maximum requests per second
- **Concurrent Users**: Multiple simultaneous users
- **Load Testing**: High-volume request handling
- **Stress Testing**: System behavior under extreme load

### **2. Test Documentation Template**

#### **Test Case Structure**
```markdown
## Test Case: [TC-001] Valid User Login

### **Objective**
Verify that a user with valid credentials can successfully authenticate and receive JWT tokens.

### **Prerequisites**
- User account exists in Keycloak
- Auth API service is running
- Valid username and password available

### **Test Steps**
1. **Send Login Request**
   - Method: POST
   - URL: `{{base_url}}/api/auth/login`
   - Headers: `Content-Type: application/json`
   - Body: Valid credentials JSON

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: access_token, refresh_token, expires_in, token_type
   - Token format: Valid JWT structure

3. **Verify Token**
   - Decode JWT token
   - Validate claims (iss, aud, exp, sub)
   - Check user information in token

### **Expected Results**
- **Status Code**: 200 OK
- **Response Body**: Contains valid JWT tokens
- **Token Expiration**: 300 seconds (5 minutes)
- **Token Type**: "Bearer"
- **User Information**: Correct user details in token

### **Test Data**
```json
{
  "username": "john.doe",
  "password": "SecurePass123"
}
```

### **Expected Response**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

### **Validation Rules**
- [ ] Status code is 200
- [ ] Response contains all required fields
- [ ] Access token is valid JWT
- [ ] Refresh token is valid JWT
- [ ] Expires_in is 300 seconds
- [ ] Token type is "Bearer"

### **Cleanup**
- No cleanup required (stateless operation)
```

## 📊 **Postman Collection Standards**

### **1. Collection Structure**
```
Nexus Platform API
├── Authentication
│   ├── Login
│   ├── Token Validation
│   ├── Token Refresh
│   └── Logout
├── User Management
│   ├── Get User Info
│   ├── Get User Groups
│   └── Update User Profile
├── Access Control
│   ├── Check Service Access
│   ├── Get User Services
│   └── Update Access Permissions
├── Admin Dashboard
│   ├── Get Services Status
│   ├── Get System Metrics
│   └── Get Service Logs
└── Health Checks
    ├── API Health
    ├── Service Health
    └── Database Health
```

### **2. Environment Variables**
```json
{
  "development": {
    "base_url": "http://localhost:8080",
    "auth_url": "http://localhost:8084",
    "admin_url": "http://localhost:8081",
    "access_control_url": "http://localhost:8083"
  },
  "staging": {
    "base_url": "https://staging-api.nexus.platform",
    "auth_url": "https://staging-auth.nexus.platform",
    "admin_url": "https://staging-admin.nexus.platform",
    "access_control_url": "https://staging-access.nexus.platform"
  },
  "production": {
    "base_url": "https://api.nexus.platform",
    "auth_url": "https://auth.nexus.platform",
    "admin_url": "https://admin.nexus.platform",
    "access_control_url": "https://access.nexus.platform"
  }
}
```

### **3. Pre-request Scripts**
```javascript
// Set common headers
pm.request.headers.add({
    key: 'Content-Type',
    value: 'application/json'
});

// Add request ID for tracking
pm.request.headers.add({
    key: 'X-Request-ID',
    value: pm.variables.replaceIn('{{$guid}}')
});

// Add authentication token if available
if (pm.environment.get('access_token')) {
    pm.request.headers.add({
        key: 'Authorization',
        value: 'Bearer ' + pm.environment.get('access_token')
    });
}
```

### **4. Test Scripts**
```javascript
// Validate response status
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Validate response time
pm.test("Response time is less than 200ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(200);
});

// Validate response structure
pm.test("Response has required fields", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access_token');
    pm.expect(jsonData).to.have.property('refresh_token');
    pm.expect(jsonData).to.have.property('expires_in');
    pm.expect(jsonData).to.have.property('token_type');
});

// Store token for subsequent requests
if (pm.response.code === 200) {
    const jsonData = pm.response.json();
    if (jsonData.access_token) {
        pm.environment.set('access_token', jsonData.access_token);
    }
    if (jsonData.refresh_token) {
        pm.environment.set('refresh_token', jsonData.refresh_token);
    }
}
```

## 🔄 **Automation Standards**

### **1. CI/CD Integration**
- **Auto-Generation**: OpenAPI specs generated during build
- **Validation**: Schema validation in CI pipeline
- **Postman Sync**: Automatic Postman collection updates
- **Documentation**: Auto-generated API documentation
- **Testing**: Automated API testing in pipeline

### **2. Version Control**
- **API Versioning**: Semantic versioning for APIs
- **Backward Compatibility**: Maintain backward compatibility
- **Deprecation Policy**: Clear deprecation timelines
- **Migration Guides**: Migration documentation for breaking changes

### **3. Monitoring Integration**
- **API Metrics**: Request/response metrics collection
- **Error Tracking**: API error monitoring and alerting
- **Performance Monitoring**: Response time and throughput tracking
- **Usage Analytics**: API usage patterns and trends

## 📈 **Success Metrics**

### **1. Documentation Quality**
- **Coverage**: 100% API endpoint documentation
- **Accuracy**: 95%+ documentation accuracy
- **Completeness**: All required fields documented
- **Examples**: Real-world examples for all endpoints

### **2. Testing Coverage**
- **Test Coverage**: 100% API endpoint test coverage
- **Test Automation**: 90%+ automated test execution
- **Test Reliability**: 95%+ test pass rate
- **Performance Testing**: Regular performance validation

### **3. Developer Experience**
- **Documentation Clarity**: Clear and understandable docs
- **Interactive Testing**: Easy-to-use Swagger UI
- **Postman Integration**: Seamless Postman collection usage
- **Error Handling**: Clear error messages and codes

This comprehensive API documentation standard ensures consistent, testable, and maintainable APIs across the Nexus Platform.
