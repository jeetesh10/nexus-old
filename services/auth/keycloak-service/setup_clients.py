#!/usr/bin/env python3
"""
Simple script to configure Keycloak clients using REST API
"""
import requests
import json
import time

def get_admin_token():
    """Get admin token from Keycloak"""
    url = "http://localhost:8080/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": "admin"
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get admin token: {response.status_code}")
        return None

def create_client(admin_token, client_data):
    """Create a client in Keycloak"""
    url = f"http://localhost:8080/admin/realms/nexus-platform/clients"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=client_data)
    if response.status_code == 201:
        print(f"✅ Created client: {client_data['clientId']}")
        return True
    else:
        print(f"❌ Failed to create client {client_data['clientId']}: {response.status_code} - {response.text}")
        return False

def main():
    print("🔐 Setting up Keycloak clients...")
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Failed to get admin token")
        return
    
    print("✅ Got admin token")
    
    # Define clients to create
    clients = [
        {
            "clientId": "nexus-landing-page",
            "name": "Nexus Landing Page",
            "enabled": True,
            "protocol": "openid-connect",
            "redirectUris": ["http://localhost:8082/*"],
            "publicClient": True,
            "authorizationServicesEnabled": True,
            "bearerOnly": False
        },
        {
            "clientId": "nexus-admin-dashboard",
            "name": "Nexus Admin Dashboard",
            "enabled": True,
            "protocol": "openid-connect",
            "redirectUris": ["http://localhost:8081/*"],
            "publicClient": True,
            "authorizationServicesEnabled": True,
            "bearerOnly": False
        },
        {
            "clientId": "nexus-api-gateway",
            "name": "Nexus API Gateway",
            "enabled": True,
            "protocol": "openid-connect",
            "redirectUris": ["https://api.nexus.platform/*"],
            "publicClient": False,
            "authorizationServicesEnabled": True,
            "bearerOnly": False
        }
    ]
    
    # Create each client
    for client in clients:
        create_client(admin_token, client)
        time.sleep(1)  # Small delay between requests
    
    print("🎉 Client setup completed!")

if __name__ == "__main__":
    main()
