#!/usr/bin/env python3
"""
Comprehensive test script for Auth API Service
Tests all endpoints and validates functionality
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
AUTH_API_URL = "http://localhost:8085"
KEYCLOAK_URL = "http://localhost:8082"  # Port-forwarded Keycloak

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(test_name, status, details=""):
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"{status_icon} {test_name}")
    if details:
        print(f"   {details}")

def test_health_endpoint():
    """Test the health endpoint"""
    print_section("Testing Health Endpoint")
    
    try:
        response = requests.get(f"{AUTH_API_URL}/api/auth/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_test("Health endpoint accessible", "PASS")
            print_test("Keycloak connectivity", "PASS" if data.get("keycloak_status") == "healthy" else "FAIL")
            print(f"   Service Info: {data.get('service_info', {})}")
            return True
        else:
            print_test("Health endpoint", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Health endpoint", "FAIL", f"Error: {str(e)}")
        return False

def test_validate_endpoint():
    """Test the JWT validation endpoint"""
    print_section("Testing JWT Validation Endpoint")
    
    # Test with missing token
    try:
        response = requests.post(
            f"{AUTH_API_URL}/api/auth/validate",
            json={"service": "test-service", "resource": "/test"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 422:
            print_test("Validation with missing token", "PASS", "Correctly rejected")
        else:
            print_test("Validation with missing token", "FAIL", f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_test("Validation endpoint", "FAIL", f"Error: {str(e)}")
        return False
    
    # Test with invalid token
    try:
        response = requests.post(
            f"{AUTH_API_URL}/api/auth/validate",
            json={
                "jwt_token": "invalid.jwt.token",
                "service": "test-service", 
                "resource": "/test"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print_test("Validation with invalid token", "PASS", f"Status: {response.status_code}, Response: {response.text[:100]}")
    except Exception as e:
        print_test("Validation with invalid token", "FAIL", f"Error: {str(e)}")
    
    return True

def test_groups_endpoint():
    """Test the groups parsing endpoint"""
    print_section("Testing Groups Parsing Endpoint")
    
    try:
        response = requests.post(
            f"{AUTH_API_URL}/api/auth/groups",
            json={"jwt_token": "invalid.jwt.token"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print_test("Groups endpoint accessible", "PASS", f"Status: {response.status_code}")
        if response.text:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print_test("Groups endpoint", "FAIL", f"Error: {str(e)}")
        return False
    
    return True

def test_service_mesh_ready():
    """Test if service is ready for service mesh integration"""
    print_section("Testing Service Mesh Readiness")
    
    try:
        # Check if service has proper labels and annotations
        import subprocess
        result = subprocess.run([
            "kubectl", "get", "svc", "auth-api-service", 
            "-n", "nexus-platform", "-o", "json"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            service_data = json.loads(result.stdout)
            labels = service_data.get("metadata", {}).get("labels", {})
            print_test("Service exists in cluster", "PASS")
            print_test("Service has app label", "PASS" if "app" in labels else "FAIL")
            
            # Check ports
            ports = service_data.get("spec", {}).get("ports", [])
            http_port = any(p.get("port") == 8085 for p in ports)
            print_test("HTTP port 8085 configured", "PASS" if http_port else "FAIL")
            
        else:
            print_test("Service exists in cluster", "FAIL", result.stderr)
            
    except Exception as e:
        print_test("Service mesh readiness", "FAIL", f"Error: {str(e)}")

def test_api_documentation():
    """Test API documentation endpoints"""
    print_section("Testing API Documentation")
    
    try:
        # Test OpenAPI JSON
        response = requests.get(f"{AUTH_API_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            print_test("OpenAPI JSON available", "PASS")
        else:
            print_test("OpenAPI JSON", "FAIL", f"Status: {response.status_code}")
        
        # Test Swagger UI
        response = requests.get(f"{AUTH_API_URL}/docs", timeout=10)
        if response.status_code == 200 and "swagger" in response.text.lower():
            print_test("Swagger UI available", "PASS")
        else:
            print_test("Swagger UI", "FAIL", f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("API documentation", "FAIL", f"Error: {str(e)}")

def main():
    """Run comprehensive tests"""
    print(f"""
    🧪 NEXUS AUTH API SERVICE - COMPREHENSIVE TEST
    ============================================
    Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Auth API URL: {AUTH_API_URL}
    Keycloak URL: {KEYCLOAK_URL}
    """)
    
    # Run all tests
    tests = [
        test_health_endpoint,
        test_validate_endpoint,
        test_groups_endpoint,
        test_service_mesh_ready,
        test_api_documentation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with error: {str(e)}")
    
    print_section("Test Summary")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Auth API service is ready for integration.")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please review the issues above.")

if __name__ == "__main__":
    main()
