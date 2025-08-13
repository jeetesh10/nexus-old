#!/usr/bin/env python3
"""
Configure CORS for Keycloak clients
"""
import requests
import json
import time

def get_admin_token():
    """Get admin token from Keycloak"""
    token_url = "http://localhost:8080/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": "AdminPass123"
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get admin token: {response.status_code}")

def update_client_cors(admin_token, client_id):
    """Update client CORS settings"""
    # First, get the current client configuration
    get_url = f"http://localhost:8080/admin/realms/nexus-platform/clients"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(get_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get clients: {response.status_code}")
        return False
    
    clients = response.json()
    target_client = None
    
    for client in clients:
        if client.get("clientId") == client_id:
            target_client = client
            break
    
    if not target_client:
        print(f"Client {client_id} not found")
        return False
    
    # Update the client with CORS settings
    update_url = f"http://localhost:8080/admin/realms/nexus-platform/clients/{target_client['id']}"
    
    # Update CORS settings
    target_client["webOrigins"] = ["http://localhost:8082"]
    target_client["redirectUris"] = ["http://localhost:8082/*"]
    target_client["publicClient"] = True
    target_client["standardFlowEnabled"] = True
    target_client["directAccessGrantsEnabled"] = True
    
    # Remove fields that shouldn't be sent in update
    update_data = {k: v for k, v in target_client.items() 
                   if k not in ["id", "clientId", "secret"]}
    
    response = requests.put(update_url, headers=headers, json=update_data)
    
    if response.status_code == 204:
        print(f"✅ Successfully updated CORS for client {client_id}")
        return True
    else:
        print(f"❌ Failed to update client {client_id}: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    print("🔧 Configuring CORS for Keycloak clients...")
    
    try:
        # Get admin token
        print("1. Getting admin token...")
        admin_token = get_admin_token()
        print("✅ Admin token obtained")
        
        # Update nexus-landing-page client
        print("2. Updating nexus-landing-page client CORS...")
        success = update_client_cors(admin_token, "nexus-landing-page")
        
        if success:
            print("\n🎉 CORS configuration completed!")
            print("You can now test the login flow again.")
        else:
            print("\n❌ CORS configuration failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
