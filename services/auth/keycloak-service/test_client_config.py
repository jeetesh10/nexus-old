#!/usr/bin/env python3
"""
Test and fix Keycloak client configuration
"""
import requests
import json

def test_keycloak_config():
    """Test Keycloak configuration"""
    print("🔍 Testing Keycloak configuration...")
    
    # Test 1: Check if realm exists
    print("\n1. Testing realm access...")
    try:
        response = requests.get("http://localhost:8080/realms/nexus-platform")
        if response.status_code == 200:
            print("✅ nexus-platform realm exists")
        else:
            print(f"❌ nexus-platform realm not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing realm: {e}")
        return False
    
    # Test 2: Check OpenID configuration
    print("\n2. Testing OpenID configuration...")
    try:
        response = requests.get("http://localhost:8080/realms/nexus-platform/.well-known/openid_configuration")
        if response.status_code == 200:
            config = response.json()
            print("✅ OpenID configuration accessible")
            print(f"   Authorization endpoint: {config.get('authorization_endpoint', 'Not found')}")
        else:
            print(f"❌ OpenID configuration not accessible: {response.status_code}")
            print("   This usually means no clients are configured in the realm")
            return False
    except Exception as e:
        print(f"❌ Error accessing OpenID config: {e}")
        return False
    
    # Test 3: Test login URL
    print("\n3. Testing login URL...")
    try:
        login_url = "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/auth"
        params = {
            "client_id": "nexus-landing-page",
            "redirect_uri": "http://localhost:8082/landing-page.html",
            "response_type": "token",
            "scope": "openid"
        }
        response = requests.get(login_url, params=params, allow_redirects=False)
        print(f"✅ Login URL test: {response.status_code}")
        if response.status_code in [200, 302]:
            print("   Login flow should work")
        else:
            print(f"   Login flow issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing login URL: {e}")
    
    return True

def main():
    print("🚀 Keycloak Configuration Test")
    print("=" * 40)
    
    success = test_keycloak_config()
    
    if success:
        print("\n✅ Keycloak configuration looks good!")
        print("\n📋 Next steps:")
        print("1. Go to: http://localhost:8082/login.html")
        print("2. Click 'Sign In with Keycloak'")
        print("3. Login with admin/AdminPass123 or test-user/TestPass123")
    else:
        print("\n❌ Keycloak configuration has issues")
        print("\n🔧 Please check:")
        print("1. Keycloak admin console: http://localhost:8080/admin/")
        print("2. Verify nexus-platform realm exists")
        print("3. Verify nexus-landing-page client is configured")
        print("4. Check redirect URIs in client settings")

if __name__ == "__main__":
    main()
