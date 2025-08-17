#!/usr/bin/env python3
"""
Test Auth API Service manually
"""
import requests
import json
import time

# Configuration
AUTH_API_URL = "http://localhost:8085"
KEYCLOAK_URL = "http://localhost:8080"
REALM = "nexus-platform"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{AUTH_API_URL}/api/auth/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"📊 Keycloak status: {data['keycloak_status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def get_test_token():
    """Get a test token from Keycloak (if available)"""
    print("🔐 Attempting to get test token from Keycloak...")
    try:
        # Try to get token using password grant (for testing only)
        token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": "nexus-platform",
            "username": "test-user",  # Assuming test user exists
            "password": "TestPass123"
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Got test token successfully")
            return access_token
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Token request error: {e}")
        return None

def test_validate_with_token(token):
    """Test validation endpoint with real token"""
    print("🧪 Testing validation with real token...")
    try:
        validate_url = f"{AUTH_API_URL}/api/auth/validate"
        
        request_data = {
            "jwt_token": token,
            "resource": "id-service",
            "client_context": "nexus",
            "action": "read"
        }
        
        response = requests.post(validate_url, json=request_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Validation successful!")
            print(f"📊 Valid: {data.get('valid')}")
            print(f"🔓 Allowed: {data.get('allowed')}")
            print(f"👤 User: {data.get('user_context', {}).get('username')}")
            print(f"📝 Permissions: {data.get('permissions')}")
            return True
        else:
            print(f"❌ Validation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def test_validate_with_fake_token():
    """Test validation endpoint with fake token"""
    print("🧪 Testing validation with fake token...")
    try:
        validate_url = f"{AUTH_API_URL}/api/auth/validate"
        
        request_data = {
            "jwt_token": "fake.jwt.token",
            "resource": "id-service",
            "client_context": "nexus",
            "action": "read"
        }
        
        response = requests.post(validate_url, json=request_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid') and not data.get('allowed'):
                print("✅ Fake token correctly rejected!")
                print(f"❌ Valid: {data.get('valid')}")
                print(f"❌ Allowed: {data.get('allowed')}")
                print(f"📝 Error: {data.get('error')}")
                return True
            else:
                print("❌ Fake token was incorrectly accepted!")
                return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Auth API Service Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    health_ok = test_health()
    print()
    
    if not health_ok:
        print("❌ Health check failed. Is the service running?")
        print("💡 Try: cd services/auth-api-service && ./start.sh")
        return
    
    # Test 2: Fake token validation
    fake_token_ok = test_validate_with_fake_token()
    print()
    
    # Test 3: Real token validation (if Keycloak is available)
    real_token = get_test_token()
    if real_token:
        test_validate_with_token(real_token)
    else:
        print("⚠️ Skipping real token test - Keycloak not available or no test user")
    
    print()
    print("🎯 Test Summary:")
    print(f"  Health Check: {'✅' if health_ok else '❌'}")
    print(f"  Fake Token Rejection: {'✅' if fake_token_ok else '❌'}")
    print(f"  Real Token Test: {'✅' if real_token else '⚠️ Skipped'}")
    
    if health_ok and fake_token_ok:
        print("\n🎉 Auth API Service is working correctly!")
        print("📋 Next steps:")
        print("  1. Set up Keycloak with test users")
        print("  2. Configure group hierarchy")
        print("  3. Test with real authentication flows")
    else:
        print("\n❌ Some tests failed. Check the service configuration.")

if __name__ == "__main__":
    main()
