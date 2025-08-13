#!/usr/bin/env python3
"""
Quick test for the login flow
"""
import requests

def test_login_flow():
    print("🧪 Testing login flow...")
    
    # Test the login URL directly
    login_url = "http://localhost:8080/realms/nexus-platform/protocol/openid-connect/auth"
    params = {
        "client_id": "nexus-landing-page",
        "redirect_uri": "http://localhost:8082/landing-page.html",
        "response_type": "token",
        "scope": "openid"
    }
    
    try:
        response = requests.get(login_url, params=params, allow_redirects=False)
        print(f"Login URL response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login page should be accessible")
            print("   You should see the Keycloak login form")
        elif response.status_code == 302:
            print("✅ Redirect happening (might be to login page)")
            print(f"   Redirect location: {response.headers.get('Location', 'Not found')}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing login flow: {e}")

if __name__ == "__main__":
    test_login_flow()
