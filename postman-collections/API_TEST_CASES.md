# API Test Cases - Nexus Platform

This document contains test cases for all API endpoints.

## Test Cases

## Test Case: [TC-001] Health check

### **Objective**
Check the health status of the Auth API service

### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send GET Request**
   - Method: GET
   - URL: `{{base_url}}/health`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-002] User login

### **Objective**
Authenticate user with username and password and return JWT tokens.

This endpoint validates user credentials against Keycloak and returns access and refresh tokens.
The access token is valid for 5 minutes and the refresh token for 30 minutes.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send POST Request**
   - Method: POST
   - URL: `{{base_url}}/login`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-003] Validate JWT token

### **Objective**
Validate a JWT token and return token information.

This endpoint validates the token signature, expiration, and claims.
Returns detailed token information if valid.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send GET Request**
   - Method: GET
   - URL: `{{base_url}}/validate-token`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-004] Get user information

### **Objective**
Get detailed user information from JWT token.

This endpoint extracts user information from the provided JWT token.
Returns user details including groups and roles.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send GET Request**
   - Method: GET
   - URL: `{{base_url}}/user-info`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-005] Get user groups

### **Objective**
Get user groups from JWT token.

This endpoint extracts user groups from the provided JWT token.
Returns list of groups the user belongs to.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send GET Request**
   - Method: GET
   - URL: `{{base_url}}/user-groups`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-006] Refresh access token

### **Objective**
Refresh an access token using a refresh token.

This endpoint uses a valid refresh token to generate a new access token.
The refresh token must not be expired.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send POST Request**
   - Method: POST
   - URL: `{{base_url}}/refresh-token`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-007] User logout

### **Objective**
Logout user and invalidate refresh token.

This endpoint invalidates the provided refresh token, effectively logging out the user.
The access token will remain valid until it expires.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send POST Request**
   - Method: POST
   - URL: `{{base_url}}/logout`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
## Test Case: [TC-008] Get OpenID Connect configuration

### **Objective**
Get OpenID Connect configuration from Keycloak.

This endpoint returns the OpenID Connect discovery document from Keycloak,
containing endpoints and configuration information.


### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send GET Request**
   - Method: GET
   - URL: `{{base_url}}/openid-config`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{
  // Test data will be populated from examples
}
```

### **Expected Response**
```json
{
  // Expected response structure
}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
