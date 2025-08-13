# API Test Cases - Nexus Platform Auth API

This document contains detailed test cases for all Auth API endpoints with step-by-step instructions and expected results.

## 📋 **Test Overview**

### **Test Categories**
- **Authentication Tests**: Login, logout, token validation
- **User Management Tests**: User info, groups retrieval
- **Token Management Tests**: Token refresh, validation
- **Error Handling Tests**: Invalid requests, error responses
- **Performance Tests**: Response time validation
- **Security Tests**: Authentication and authorization

### **Test Environment Setup**
- **Base URL**: `http://localhost:8084/api/auth`
- **Test User**: `john.doe` / `SecurePass123`
- **Expected Response Time**: < 200ms
- **Authentication**: JWT Bearer tokens

## 🧪 **Test Cases**

### **Authentication Tests**

#### **Test Case: [TC-001] Valid User Login**

**Objective**: Verify that a user with valid credentials can successfully authenticate and receive JWT tokens.

**Prerequisites**:
- Auth API service is running
- User account exists in Keycloak
- Valid username and password available

**Test Steps**:
1. **Send Login Request**
   - Method: POST
   - URL: `{{base_url}}/login`
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

**Test Data**:
```json
{
  "username": "john.doe",
  "password": "SecurePass123"
}
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Response contains all required fields
- [ ] Access token is valid JWT
- [ ] Refresh token is valid JWT
- [ ] Expires_in is 300 seconds
- [ ] Token type is "Bearer"

**Cleanup**: No cleanup required (stateless operation)

---

#### **Test Case: [TC-002] Invalid Credentials Login**

**Objective**: Verify that login fails with invalid credentials and returns appropriate error.

**Prerequisites**:
- Auth API service is running
- Invalid credentials available

**Test Steps**:
1. **Send Login Request**
   - Method: POST
   - URL: `{{base_url}}/login`
   - Headers: `Content-Type: application/json`
   - Body: Invalid credentials JSON

2. **Validate Error Response**
   - Status Code: 401 Unauthorized
   - Error structure: error, error_description, status_code
   - Error message: "Invalid username or password"

**Test Data**:
```json
{
  "username": "invalid",
  "password": "wrong"
}
```

**Expected Response**:
```json
{
  "error": "invalid_credentials",
  "error_description": "Invalid username or password",
  "status_code": 401,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 401
- [ ] Error code is "invalid_credentials"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

#### **Test Case: [TC-003] Missing Credentials Login**

**Objective**: Verify that login fails when credentials are missing and returns appropriate error.

**Prerequisites**:
- Auth API service is running

**Test Steps**:
1. **Send Login Request**
   - Method: POST
   - URL: `{{base_url}}/login`
   - Headers: `Content-Type: application/json`
   - Body: Empty or missing credentials

2. **Validate Error Response**
   - Status Code: 400 Bad Request
   - Error structure: error, error_description, status_code
   - Error message: "Username and password are required"

**Test Data**:
```json
{
  "username": "",
  "password": ""
}
```

**Expected Response**:
```json
{
  "error": "missing_credentials",
  "error_description": "Username and password are required",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 400
- [ ] Error code is "missing_credentials"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

### **Token Validation Tests**

#### **Test Case: [TC-004] Valid Token Validation**

**Objective**: Verify that a valid JWT token is properly validated and returns token information.

**Prerequisites**:
- Auth API service is running
- Valid JWT token available (from successful login)

**Test Steps**:
1. **Send Token Validation Request**
   - Method: GET
   - URL: `{{base_url}}/validate-token?token={{access_token}}`
   - Headers: None required

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: valid, user_id, username, email, exp, iat
   - Valid field is true

**Test Data**:
```
Token: {{access_token}} (from previous login)
```

**Expected Response**:
```json
{
  "valid": true,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "exp": 1640995200,
  "iat": 1640908800
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Valid field is true
- [ ] User information is correct
- [ ] Token timestamps are valid

**Cleanup**: No cleanup required

---

#### **Test Case: [TC-005] Invalid Token Validation**

**Objective**: Verify that an invalid JWT token is properly rejected.

**Prerequisites**:
- Auth API service is running
- Invalid JWT token available

**Test Steps**:
1. **Send Token Validation Request**
   - Method: GET
   - URL: `{{base_url}}/validate-token?token=invalid_token`
   - Headers: None required

2. **Validate Error Response**
   - Status Code: 401 Unauthorized
   - Error structure: error, error_description, status_code
   - Error message: "Token is invalid or expired"

**Test Data**:
```
Token: invalid_token
```

**Expected Response**:
```json
{
  "error": "invalid_token",
  "error_description": "Token is invalid or expired",
  "status_code": 401,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 401
- [ ] Error code is "invalid_token"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

#### **Test Case: [TC-006] Missing Token Validation**

**Objective**: Verify that token validation fails when token is missing.

**Prerequisites**:
- Auth API service is running

**Test Steps**:
1. **Send Token Validation Request**
   - Method: GET
   - URL: `{{base_url}}/validate-token`
   - Headers: None required

2. **Validate Error Response**
   - Status Code: 400 Bad Request
   - Error structure: error, error_description, status_code
   - Error message: "Token parameter is required"

**Test Data**:
```
Token: (missing)
```

**Expected Response**:
```json
{
  "error": "missing_token",
  "error_description": "Token parameter is required",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 400
- [ ] Error code is "missing_token"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

### **User Management Tests**

#### **Test Case: [TC-007] Get User Information**

**Objective**: Verify that user information can be retrieved from a valid JWT token.

**Prerequisites**:
- Auth API service is running
- Valid JWT token available (from successful login)

**Test Steps**:
1. **Send User Info Request**
   - Method: GET
   - URL: `{{base_url}}/user-info?token={{access_token}}`
   - Headers: None required

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: user_id, username, email, name, groups, roles
   - User information is accurate

**Test Data**:
```
Token: {{access_token}} (from previous login)
```

**Expected Response**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "groups": ["nexus", "platform-admin"],
  "roles": ["admin", "user"]
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] User ID is correct
- [ ] Username matches login
- [ ] Groups and roles are present
- [ ] All required fields are present

**Cleanup**: No cleanup required

---

#### **Test Case: [TC-008] Get User Groups**

**Objective**: Verify that user groups can be retrieved from a valid JWT token.

**Prerequisites**:
- Auth API service is running
- Valid JWT token available (from successful login)

**Test Steps**:
1. **Send User Groups Request**
   - Method: GET
   - URL: `{{base_url}}/user-groups?token={{access_token}}`
   - Headers: None required

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: groups array
   - Groups are accurate for the user

**Test Data**:
```
Token: {{access_token}} (from previous login)
```

**Expected Response**:
```json
{
  "groups": ["nexus", "platform-admin", "admin-dashboard"]
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Groups array is present
- [ ] Groups match user permissions
- [ ] Array is not empty

**Cleanup**: No cleanup required

---

### **Token Management Tests**

#### **Test Case: [TC-009] Refresh Access Token**

**Objective**: Verify that an access token can be refreshed using a valid refresh token.

**Prerequisites**:
- Auth API service is running
- Valid refresh token available (from successful login)

**Test Steps**:
1. **Send Token Refresh Request**
   - Method: POST
   - URL: `{{base_url}}/refresh-token`
   - Headers: `Content-Type: application/json`
   - Body: Refresh token JSON

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: new access_token, refresh_token, expires_in
   - New tokens are different from original

**Test Data**:
```json
{
  "refresh_token": "{{refresh_token}}"
}
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "token_type": "Bearer"
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] New access token is provided
- [ ] Token expiration is correct
- [ ] Token type is "Bearer"

**Cleanup**: No cleanup required

---

#### **Test Case: [TC-010] Invalid Refresh Token**

**Objective**: Verify that token refresh fails with invalid refresh token.

**Prerequisites**:
- Auth API service is running
- Invalid refresh token available

**Test Steps**:
1. **Send Token Refresh Request**
   - Method: POST
   - URL: `{{base_url}}/refresh-token`
   - Headers: `Content-Type: application/json`
   - Body: Invalid refresh token JSON

2. **Validate Error Response**
   - Status Code: 401 Unauthorized
   - Error structure: error, error_description, status_code
   - Error message: "Invalid refresh token"

**Test Data**:
```json
{
  "refresh_token": "invalid_refresh_token"
}
```

**Expected Response**:
```json
{
  "error": "invalid_refresh_token",
  "error_description": "Invalid refresh token",
  "status_code": 401,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 401
- [ ] Error code is "invalid_refresh_token"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

### **Logout Tests**

#### **Test Case: [TC-011] User Logout**

**Objective**: Verify that a user can successfully logout and refresh token is invalidated.

**Prerequisites**:
- Auth API service is running
- Valid refresh token available (from successful login)

**Test Steps**:
1. **Send Logout Request**
   - Method: POST
   - URL: `{{base_url}}/logout`
   - Headers: `Content-Type: application/json`
   - Body: Refresh token JSON

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: success message
   - Refresh token is invalidated

3. **Verify Token Invalidation**
   - Try to refresh token again
   - Should fail with invalid token error

**Test Data**:
```json
{
  "token": "{{refresh_token}}"
}
```

**Expected Response**:
```json
{
  "message": "Logged out successfully"
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Success message is clear
- [ ] Refresh token is invalidated
- [ ] Subsequent refresh attempts fail

**Cleanup**: Clear stored tokens

---

#### **Test Case: [TC-012] Logout Without Token**

**Objective**: Verify that logout fails when token is missing.

**Prerequisites**:
- Auth API service is running

**Test Steps**:
1. **Send Logout Request**
   - Method: POST
   - URL: `{{base_url}}/logout`
   - Headers: `Content-Type: application/json`
   - Body: Empty or missing token

2. **Validate Error Response**
   - Status Code: 400 Bad Request
   - Error structure: error, error_description, status_code
   - Error message: "Token is required"

**Test Data**:
```json
{
  "token": ""
}
```

**Expected Response**:
```json
{
  "error": "missing_token",
  "error_description": "Token is required",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

**Validation Rules**:
- [ ] Status code is 400
- [ ] Error code is "missing_token"
- [ ] Error description is clear
- [ ] Request ID is present

**Cleanup**: No cleanup required

---

### **Configuration Tests**

#### **Test Case: [TC-013] Get OpenID Configuration**

**Objective**: Verify that OpenID Connect configuration can be retrieved from Keycloak.

**Prerequisites**:
- Auth API service is running
- Keycloak is accessible

**Test Steps**:
1. **Send OpenID Config Request**
   - Method: GET
   - URL: `{{base_url}}/openid-config`
   - Headers: None required

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: issuer, endpoints, supported features
   - Configuration is valid OpenID Connect format

**Test Data**:
```
No data required
```

**Expected Response**:
```json
{
  "issuer": "http://localhost:8080/realms/nexus-platform",
  "authorization_endpoint": "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/auth",
  "token_endpoint": "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/token",
  "userinfo_endpoint": "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/userinfo",
  "jwks_uri": "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/certs",
  "end_session_endpoint": "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/logout"
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Issuer is correct
- [ ] All endpoints are present
- [ ] URLs are valid

**Cleanup**: No cleanup required

---

### **Health Check Tests**

#### **Test Case: [TC-014] Health Check**

**Objective**: Verify that the Auth API service health check endpoint works correctly.

**Prerequisites**:
- Auth API service is running

**Test Steps**:
1. **Send Health Check Request**
   - Method: GET
   - URL: `{{base_url}}/health`
   - Headers: None required

2. **Validate Response**
   - Status Code: 200 OK
   - Response contains: status, timestamp, keycloak connection
   - Service is healthy

**Test Data**:
```
No data required
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "keycloak": "connected",
  "endpoints": {
    "validate_token": "/api/auth/validate-token",
    "user_info": "/api/auth/user-info",
    "user_groups": "/api/auth/user-groups",
    "login": "/api/auth/login",
    "refresh_token": "/api/auth/refresh-token",
    "logout": "/api/auth/logout",
    "openid_config": "/api/auth/openid-config"
  }
}
```

**Validation Rules**:
- [ ] Status code is 200
- [ ] Status is "healthy"
- [ ] Keycloak is "connected"
- [ ] All endpoints are listed

**Cleanup**: No cleanup required

---

## 📊 **Performance Tests**

### **Test Case: [TC-015] Response Time Validation**

**Objective**: Verify that all API endpoints respond within acceptable time limits.

**Prerequisites**:
- Auth API service is running
- Network conditions are normal

**Test Steps**:
1. **Send Requests to All Endpoints**
   - Health check: GET `/health`
   - Login: POST `/login`
   - Token validation: GET `/validate-token`
   - User info: GET `/user-info`
   - User groups: GET `/user-groups`
   - Token refresh: POST `/refresh-token`
   - Logout: POST `/logout`
   - OpenID config: GET `/openid-config`

2. **Measure Response Times**
   - Record response time for each request
   - Calculate average response time
   - Identify slow endpoints

**Expected Results**:
- **Individual Response Time**: < 200ms per request
- **Average Response Time**: < 150ms
- **95th Percentile**: < 300ms
- **No Timeouts**: All requests complete successfully

**Validation Rules**:
- [ ] All endpoints respond within 200ms
- [ ] Average response time < 150ms
- [ ] No timeouts occur
- [ ] Performance is consistent

**Cleanup**: No cleanup required

---

### **Test Case: [TC-016] Load Testing**

**Objective**: Verify that the Auth API can handle multiple concurrent requests.

**Prerequisites**:
- Auth API service is running
- Load testing tool available (e.g., Apache Bench, wrk)

**Test Steps**:
1. **Run Load Tests**
   - Concurrent users: 10, 50, 100
   - Duration: 30 seconds each
   - Endpoints: Login, token validation, user info

2. **Monitor Performance**
   - Response times under load
   - Error rates
   - Throughput (requests per second)

**Expected Results**:
- **10 Concurrent Users**: < 300ms average response time
- **50 Concurrent Users**: < 500ms average response time
- **100 Concurrent Users**: < 1000ms average response time
- **Error Rate**: < 1%
- **Throughput**: > 100 requests/second

**Validation Rules**:
- [ ] Response times within limits
- [ ] Error rate < 1%
- [ ] Throughput > 100 req/sec
- [ ] Service remains stable

**Cleanup**: No cleanup required

---

## 🔒 **Security Tests**

### **Test Case: [TC-017] Authentication Bypass**

**Objective**: Verify that protected endpoints cannot be accessed without authentication.

**Prerequisites**:
- Auth API service is running
- Protected endpoints identified

**Test Steps**:
1. **Access Protected Endpoints Without Token**
   - User info: GET `/user-info`
   - User groups: GET `/user-groups`
   - Token refresh: POST `/refresh-token`
   - Logout: POST `/logout`

2. **Validate Security Response**
   - Status Code: 401 Unauthorized
   - Error message indicates authentication required
   - No sensitive data exposed

**Expected Results**:
- **Status Code**: 401 for all protected endpoints
- **Error Message**: Clear authentication requirement
- **No Data Exposure**: No sensitive information in response

**Validation Rules**:
- [ ] All protected endpoints return 401
- [ ] Error messages are clear
- [ ] No sensitive data exposed
- [ ] Security headers present

**Cleanup**: No cleanup required

---

### **Test Case: [TC-018] Token Tampering**

**Objective**: Verify that tampered JWT tokens are properly rejected.

**Prerequisites**:
- Auth API service is running
- Valid JWT token available

**Test Steps**:
1. **Modify JWT Token**
   - Change payload data
   - Modify signature
   - Use expired token

2. **Test Modified Tokens**
   - Token validation: GET `/validate-token`
   - User info: GET `/user-info`
   - User groups: GET `/user-groups`

3. **Validate Security Response**
   - Status Code: 401 Unauthorized
   - Error message indicates invalid token
   - No access granted

**Expected Results**:
- **Status Code**: 401 for all tampered tokens
- **Error Message**: "Token is invalid or expired"
- **No Access**: No sensitive data returned

**Validation Rules**:
- [ ] All tampered tokens rejected
- [ ] Clear error messages
- [ ] No unauthorized access
- [ ] Security maintained

**Cleanup**: No cleanup required

---

## 📝 **Test Execution Guide**

### **Manual Testing**
1. **Setup Environment**
   - Start Auth API service
   - Ensure Keycloak is running
   - Prepare test data

2. **Run Test Cases**
   - Execute tests in order
   - Record results
   - Document any issues

3. **Validate Results**
   - Check status codes
   - Verify response structure
   - Confirm error handling

### **Automated Testing**
1. **Import Postman Collection**
   - Use generated collection
   - Set up environment variables
   - Configure test data

2. **Run Test Suite**
   - Execute all tests
   - Review test results
   - Address failures

3. **Performance Testing**
   - Use load testing tools
   - Monitor system resources
   - Validate performance metrics

### **Continuous Integration**
1. **Automated Test Execution**
   - Run tests on every build
   - Validate API changes
   - Ensure regression prevention

2. **Test Reporting**
   - Generate test reports
   - Track test coverage
   - Monitor test trends

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] All endpoints respond correctly
- [ ] Authentication works properly
- [ ] Error handling is appropriate
- [ ] Data validation is effective

### **Performance Requirements**
- [ ] Response time < 200ms
- [ ] Throughput > 100 req/sec
- [ ] Error rate < 1%
- [ ] System stability maintained

### **Security Requirements**
- [ ] Authentication bypass prevented
- [ ] Token tampering detected
- [ ] Sensitive data protected
- [ ] Security headers present

### **Quality Requirements**
- [ ] 100% test coverage
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Standards compliance

This comprehensive test documentation ensures thorough validation of the Auth API functionality, performance, and security.
