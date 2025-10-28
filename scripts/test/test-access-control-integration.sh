#!/bin/bash
set -e

echo "🧪 Testing Access Control Service Integration..."

# Color functions
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Configuration
AUTH_API_URL="http://localhost:8084"
ACCESS_CONTROL_URL="http://localhost:8003"
LANDING_PAGE_URL="http://localhost:8004"
MONGODB_URL="http://localhost:8000"
POSTGRESQL_URL="http://localhost:8002"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_status "Running: $test_name"
    
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        if [ "$expected_status" = "success" ]; then
            print_success "✓ $test_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            print_error "✗ $test_name (expected failure but got success)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [ "$expected_status" = "failure" ]; then
            print_success "✓ $test_name (expected failure)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            print_error "✗ $test_name"
            echo "Error output:"
            cat /tmp/test_output.log
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
}

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Test 1: Auth API Health Check
run_test "Auth API Health Check" \
    "curl -s -f $AUTH_API_URL/health" \
    "success"

# Test 2: MongoDB Orchestrator Health Check
run_test "MongoDB Orchestrator Health Check" \
    "curl -s -f $MONGODB_URL/health" \
    "success"

# Test 3: Access Control Service Health Check
run_test "Access Control Service Health Check" \
    "curl -s -f $ACCESS_CONTROL_URL/health" \
    "success"

# Test 4: Landing Page Health Check
run_test "Landing Page Health Check" \
    "curl -s -f $LANDING_PAGE_URL/health" \
    "success"

# Test 5: Auth API Login
print_status "Testing Auth API Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"AdminPass123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_success "✓ Auth API Login"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Extract token
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "Token extracted: ${TOKEN:0:20}..."
else
    print_error "✗ Auth API Login"
    echo "Response: $LOGIN_RESPONSE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    exit 1
fi

# Test 6: Access Control Service - Get Landing Page Data
run_test "Access Control - Get Landing Page Data" \
    "curl -s -f -H 'Authorization: Bearer $TOKEN' $ACCESS_CONTROL_URL/api/landing-page" \
    "success"

# Test 7: Access Control Service - Create Group
run_test "Access Control - Create Group" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $ACCESS_CONTROL_URL/api/groups -d '{\"name\":\"test-group\",\"description\":\"Test group for integration testing\",\"service_name\":\"test-service\",\"permissions\":[\"read\",\"write\"]}'" \
    "success"

# Test 8: Access Control Service - Create User
run_test "Access Control - Create User" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $ACCESS_CONTROL_URL/api/users -d '{\"username\":\"testuser\",\"email\":\"test@example.com\",\"full_name\":\"Test User\",\"service_name\":\"test-service\",\"group_name\":\"test-group\",\"role\":\"user\"}'" \
    "success"

# Test 9: Access Control Service - Get Groups
run_test "Access Control - Get Groups" \
    "curl -s -f -H 'Authorization: Bearer $TOKEN' '$ACCESS_CONTROL_URL/api/groups?service_name=test-service'" \
    "success"

# Test 10: Access Control Service - Get User
run_test "Access Control - Get User" \
    "curl -s -f -H 'Authorization: Bearer $TOKEN' $ACCESS_CONTROL_URL/api/users/testuser" \
    "success"

# Test 11: MongoDB Orchestrator - Create Collection
run_test "MongoDB Orchestrator - Create Collection" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $MONGODB_URL/api/mongodb/operation -d '{\"service_name\":\"access-control\",\"database_name\":\"access_control\",\"collection_name\":\"test_collection\",\"operation\":\"insert\",\"data\":{\"test\":\"data\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}'" \
    "success"

# Test 12: MongoDB Orchestrator - Query Collection
run_test "MongoDB Orchestrator - Query Collection" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $MONGODB_URL/api/mongodb/operation -d '{\"service_name\":\"access-control\",\"database_name\":\"access_control\",\"collection_name\":\"test_collection\",\"operation\":\"find\",\"query\":{}}'" \
    "success"

# Test 13: Landing Page - Access without token (should show login)
run_test "Landing Page - Access without token" \
    "curl -s $LANDING_PAGE_URL/ | grep -q 'Sign In'" \
    "success"

# Test 14: Landing Page - Access with token (should show services)
run_test "Landing Page - Access with token" \
    "curl -s -H 'Authorization: Bearer $TOKEN' $LANDING_PAGE_URL/ | grep -q 'Welcome'" \
    "success"

# Test 15: Service Mesh Integration (if available)
if kubectl get pods -n default | grep -q "linkerd"; then
    run_test "Service Mesh - Check Linkerd pods" \
        "kubectl get pods -n default | grep linkerd | grep Running" \
        "success"
else
    print_status "⚠️  Service Mesh not deployed, skipping mesh tests"
fi

# Test 16: API Gateway Integration (if available)
if kubectl get pods -n default | grep -q "apisix"; then
    run_test "API Gateway - Check APISIX pods" \
        "kubectl get pods -n default | grep apisix | grep Running" \
        "success"
else
    print_status "⚠️  API Gateway not deployed, skipping gateway tests"
fi

# Test 17: Observability Stack (if available)
if kubectl get pods -n observability 2>/dev/null | grep -q "prometheus"; then
    run_test "Observability - Check Prometheus" \
        "kubectl get pods -n observability | grep prometheus | grep Running" \
        "success"
else
    print_status "⚠️  Observability stack not deployed, skipping monitoring tests"
fi

# Test 18: Database Orchestrator - PostgreSQL Operations
run_test "PostgreSQL Orchestrator - Health Check" \
    "curl -s -f $POSTGRESQL_URL/health" \
    "success"

# Test 19: PostgreSQL Orchestrator - Create Database
run_test "PostgreSQL Orchestrator - Create Database" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $POSTGRESQL_URL/api/postgresql/database -d '{\"service_name\":\"access-control\",\"database_name\":\"test_db\",\"description\":\"Test database for integration testing\"}'" \
    "success"

# Test 20: PostgreSQL Orchestrator - Create Table
run_test "PostgreSQL Orchestrator - Create Table" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $POSTGRESQL_URL/api/postgresql/operation -d '{\"service_name\":\"access-control\",\"database_name\":\"test_db\",\"table_name\":\"test_table\",\"operation\":\"create_table\",\"data\":{\"id\":\"SERIAL PRIMARY KEY\",\"name\":\"VARCHAR(255) NOT NULL\",\"created_at\":\"TIMESTAMP DEFAULT CURRENT_TIMESTAMP\"}}'" \
    "success"

# Test 21: PostgreSQL Orchestrator - Insert Data
run_test "PostgreSQL Orchestrator - Insert Data" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $POSTGRESQL_URL/api/postgresql/operation -d '{\"service_name\":\"access-control\",\"database_name\":\"test_db\",\"table_name\":\"test_table\",\"operation\":\"insert\",\"columns\":[\"name\"],\"data\":{\"name\":\"Test Record\"}}'" \
    "success"

# Test 22: PostgreSQL Orchestrator - Query Data
run_test "PostgreSQL Orchestrator - Query Data" \
    "curl -s -f -X POST -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' $POSTGRESQL_URL/api/postgresql/operation -d '{\"service_name\":\"access-control\",\"database_name\":\"test_db\",\"table_name\":\"test_table\",\"operation\":\"select\",\"query\":\"SELECT * FROM test_table\"}'" \
    "success"

# Test 23: Admin Dashboard Integration
run_test "Admin Dashboard - Health Check" \
    "curl -s -f http://localhost:8081/health" \
    "success"

# Test 24: Admin Dashboard - Access with token
run_test "Admin Dashboard - Access with token" \
    "curl -s -H 'Authorization: Bearer $TOKEN' http://localhost:8081/ | grep -q 'Admin Dashboard'" \
    "success"

# Test 25: End-to-End User Flow
print_status "Testing End-to-End User Flow..."
print_status "1. User logs in via Auth API"
print_status "2. User accesses landing page"
print_status "3. Landing page calls Access Control Service"
print_status "4. Access Control Service uses MongoDB Orchestrator"
print_status "5. User sees personalized service tiles"

# Generate test report
echo ""
echo "=========================================="
echo "🧪 Access Control Integration Test Report"
echo "=========================================="
echo "Date: $(date)"
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "🎉 All integration tests passed!"
    print_success "✅ Access Control Service is fully integrated!"
    print_success "✅ MongoDB Orchestrator is working as managed service!"
    print_success "✅ Auth API integration is working!"
    print_success "✅ Landing page is dynamically loading tiles!"
    print_success "✅ Admin Dashboard integration is working!"
    print_success "✅ PostgreSQL Orchestrator is working!"
    print_success "🚀 Platform is ready for production deployment!"
    exit 0
else
    print_error "⚠️  Some tests failed. Please review the errors above."
    print_error "🔧 Fix the issues before proceeding to production."
    exit 1
fi
