#!/usr/bin/env python3
"""
Script to get JWT token from Keycloak for testing Auth API service
"""
import requests
import json
import sys
from datetime import datetime, timedelta
import jwt
import base64

# Keycloak configuration
KEYCLOAK_URL = "http://localhost:8083"
REALM = "master"
CLIENT_ID = "admin-cli"

def get_admin_token():
    """Get admin token from Keycloak"""
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    # Try different admin credentials
    credentials = [
        {"username": "admin", "password": "Z5NrQ7ooeP8RlZsEgCyFlYGds"},
        {"username": "admin", "password": "admin"},
        {"username": "keycloak", "password": "keycloak"},
    ]
    
    for cred in credentials:
        data = {
            "username": cred["username"],
            "password": cred["password"],
            "grant_type": "password",
            "client_id": CLIENT_ID
        }
        
        try:
            response = requests.post(url, data=data)
            print(f"Trying credentials: {cred['username']}")
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ Successfully got admin token!")
                return token_data["access_token"]
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None

def create_test_jwt():
    """Create a test JWT token manually for testing purposes"""
    print("\n🔧 Creating test JWT token...")
    
    # JWT Header
    header = {
        "alg": "RS256",
        "typ": "JWT",
        "kid": "test-key"
    }
    
    # JWT Payload with groups
    payload = {
        "iss": f"{KEYCLOAK_URL}/realms/{REALM}",
        "sub": "test-user-123",
        "aud": "account",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp()),
        "auth_time": int(datetime.now().timestamp()),
        "jti": "test-jwt-id",
        "email": "test@example.com",
        "preferred_username": "testuser",
        "realm_access": {
            "roles": ["user"]
        },
        "groups": [
            "/admin",
            "/admin/platform",
            "/users",
            "/users/developers",
            "/services",
            "/services/mongodb",
            "/services/neo4j"
        ],
        "resource_access": {
            "account": {
                "roles": ["manage-account", "manage-account-links", "view-profile"]
            }
        }
    }
    
    # For testing, we'll create an unsigned token (algorithm: none)
    # This is for testing purposes only - never use in production
    test_token = jwt.encode(payload, "", algorithm="none")
    
    print(f"✅ Test JWT Token created!")
    print(f"📋 Token (first 100 chars): {test_token[:100]}...")
    print(f"📋 Full token: {test_token}")
    
    # Decode and show the payload
    decoded = jwt.decode(test_token, options={"verify_signature": False})
    print(f"\n📄 Token payload:")
    print(json.dumps(decoded, indent=2))
    
    return test_token

def test_realms():
    """Test available realms"""
    print("\n🔍 Testing available realms...")
    try:
        response = requests.get(f"{KEYCLOAK_URL}/auth/realms")
        if response.status_code == 200:
            print("✅ Realms endpoint (auth/realms) accessible")
            print(response.text[:200])
        else:
            print(f"❌ Realms endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing realms: {e}")
    
    # Try the new format
    try:
        response = requests.get(f"{KEYCLOAK_URL}/realms/master")
        if response.status_code == 200:
            print("✅ Master realm accessible")
            data = response.json()
            print(f"Realm: {data.get('realm')}")
            print(f"Token service: {data.get('token-service')}")
        else:
            print(f"❌ Master realm failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing master realm: {e}")

def main():
    print("🔑 Keycloak JWT Token Generator for Auth API Testing")
    print("=" * 60)
    
    # Test Keycloak connectivity
    try:
        response = requests.get(f"{KEYCLOAK_URL}/realms/master")
        if response.status_code != 200:
            print(f"❌ Cannot connect to Keycloak at {KEYCLOAK_URL}")
            print("Please ensure Keycloak port-forward is running:")
            print("kubectl port-forward svc/keycloak-service -n keycloak 8083:8080")
            return
        else:
            print(f"✅ Keycloak is accessible at {KEYCLOAK_URL}")
    except Exception as e:
        print(f"❌ Cannot connect to Keycloak: {e}")
        return
    
    # Test realms
    test_realms()
    
    # Try to get admin token
    admin_token = get_admin_token()
    
    if admin_token:
        print(f"\n✅ Admin token obtained (first 50 chars): {admin_token[:50]}...")
        
        # You can use this admin token to create users, clients, etc.
        print("\n📋 Admin token for API calls:")
        print(admin_token)
        
    else:
        print("\n⚠️  Could not get admin token, creating test JWT for Auth API testing...")
        test_token = create_test_jwt()
        
        print("\n📋 Use this test token to test your Auth API service:")
        print("=" * 60)
        print(f"Bearer {test_token}")
        print("=" * 60)
        
        print("\n🧪 Test commands:")
        print(f"curl -X POST 'http://localhost:8085/api/auth/validate' \\")
        print(f"  -H 'Authorization: Bearer {test_token}' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"jwt_token\": \"{test_token}\", \"service\": \"test-service\", \"resource\": \"/test\"}}'")
        
        print(f"\ncurl -X POST 'http://localhost:8085/api/auth/groups' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"jwt_token\": \"{test_token}\"}}'")

if __name__ == "__main__":
    main()
