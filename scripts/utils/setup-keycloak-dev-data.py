#!/usr/bin/env python3
"""
Setup Keycloak development data
- Create nexus-client
- Create 10 test users (Test1-Test10)
- Create group hierarchy based on the provided structure
- Assign users to different groups for testing
"""

import requests
import json
import sys
import time
from typing import Dict, List

class KeycloakSetup:
    def __init__(self, base_url: str, admin_username: str, admin_password: str):
        self.base_url = base_url
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_token = None
        self.realm = "nexus"
        
    def get_admin_token(self) -> str:
        """Get admin access token for API calls"""
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            return self.admin_token
        else:
            print(f"Failed to get admin token: {response.status_code} - {response.text}")
            sys.exit(1)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with admin token"""
        if not self.admin_token:
            self.get_admin_token()
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def create_client(self) -> str:
        """Create nexus-client and return client secret"""
        print("Creating nexus-client...")
        
        client_data = {
            "clientId": "nexus-client",
            "name": "Nexus Application Client",
            "description": "Client for Nexus platform services",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "publicClient": False,
            "protocol": "openid-connect",
            "redirectUris": ["http://localhost:8085/*"],
            "webOrigins": ["http://localhost:8085"],
            "attributes": {
                "access.token.lifespan": "3600",
                "client.secret.creation.time": str(int(time.time()))
            }
        }
        
        url = f"{self.base_url}/admin/realms/{self.realm}/clients"
        response = requests.post(url, headers=self.get_headers(), json=client_data)
        
        if response.status_code == 201:
            print("✓ Client created successfully")
            # Get the client to retrieve the secret
            clients_response = requests.get(url, headers=self.get_headers(), params={"clientId": "nexus-client"})
            if clients_response.status_code == 200:
                client = clients_response.json()[0]
                client_id = client["id"]
                
                # Get client secret
                secret_url = f"{self.base_url}/admin/realms/{self.realm}/clients/{client_id}/client-secret"
                secret_response = requests.get(secret_url, headers=self.get_headers())
                if secret_response.status_code == 200:
                    secret = secret_response.json()["value"]
                    print(f"✓ Client secret: {secret}")
                    return secret
        else:
            print(f"Failed to create client: {response.status_code} - {response.text}")
            return None
    
    def create_groups(self):
        """Create group hierarchy"""
        print("Creating group hierarchy...")
        
        # Define group structure based on your hierarchy
        groups = [
            # Top level groups
            {"name": "Nexus", "path": "/Nexus"},
            {"name": "Acme", "path": "/Acme"},
            
            # Nexus subgroups
            {"name": "Employee", "path": "/Nexus/Employee", "parent": "Nexus"},
            {"name": "ID_services", "path": "/Nexus/ID_services", "parent": "Nexus"},
            {"name": "MongoService", "path": "/Nexus/MongoService", "parent": "Nexus"},
            
            # Nexus Employee roles
            {"name": "Developer", "path": "/Nexus/Employee/Developer", "parent": "Employee"},
            {"name": "Tester", "path": "/Nexus/Employee/Tester", "parent": "Employee"},
            {"name": "App_admin", "path": "/Nexus/Employee/App_admin", "parent": "Employee"},
            {"name": "Admin", "path": "/Nexus/Employee/Admin", "parent": "Employee"},
            {"name": "Customer", "path": "/Nexus/Employee/Customer", "parent": "Employee"},
            
            # ID services structure
            {"name": "Role", "path": "/Nexus/ID_services/Role", "parent": "ID_services"},
            {"name": "Subscription", "path": "/Nexus/ID_services/Subscription", "parent": "ID_services"},
            {"name": "Admin", "path": "/Nexus/ID_services/Role/Admin", "parent": "Role"},
            {"name": "Customer", "path": "/Nexus/ID_services/Role/Customer", "parent": "Role"},
            {"name": "Basic", "path": "/Nexus/ID_services/Subscription/Basic", "parent": "Subscription"},
            {"name": "Pro", "path": "/Nexus/ID_services/Subscription/Pro", "parent": "Subscription"},
            {"name": "Pro+", "path": "/Nexus/ID_services/Subscription/Pro+", "parent": "Subscription"},
            
            # MongoService structure (similar to ID services)
            {"name": "Role", "path": "/Nexus/MongoService/Role", "parent": "MongoService"},
            {"name": "Subscription", "path": "/Nexus/MongoService/Subscription", "parent": "MongoService"},
            {"name": "Admin", "path": "/Nexus/MongoService/Role/Admin", "parent": "Role"},
            {"name": "Customer", "path": "/Nexus/MongoService/Role/Customer", "parent": "Role"},
            {"name": "Basic", "path": "/Nexus/MongoService/Subscription/Basic", "parent": "Subscription"},
            {"name": "Pro", "path": "/Nexus/MongoService/Subscription/Pro", "parent": "Subscription"},
            {"name": "Pro+", "path": "/Nexus/MongoService/Subscription/Pro+", "parent": "Subscription"},
        ]
        
        created_groups = {}
        url = f"{self.base_url}/admin/realms/{self.realm}/groups"
        
        # Create groups in order (parents first)
        for group in groups:
            group_data = {
                "name": group["name"],
                "path": group["path"]
            }
            
            if "parent" not in group:
                # Top-level group
                response = requests.post(url, headers=self.get_headers(), json=group_data)
                if response.status_code == 201:
                    print(f"✓ Created group: {group['name']}")
                    # Get the created group ID
                    groups_response = requests.get(url, headers=self.get_headers())
                    for g in groups_response.json():
                        if g["name"] == group["name"]:
                            created_groups[group["name"]] = g["id"]
                            break
                else:
                    print(f"Failed to create group {group['name']}: {response.status_code}")
            else:
                # Child group
                parent_id = created_groups.get(group["parent"])
                if parent_id:
                    child_url = f"{url}/{parent_id}/children"
                    response = requests.post(child_url, headers=self.get_headers(), json=group_data)
                    if response.status_code == 201:
                        print(f"✓ Created subgroup: {group['path']}")
                        # Get the created subgroup ID
                        parent_response = requests.get(f"{url}/{parent_id}/children", headers=self.get_headers())
                        for g in parent_response.json():
                            if g["name"] == group["name"]:
                                created_groups[group["name"]] = g["id"]
                                break
                    else:
                        print(f"Failed to create subgroup {group['name']}: {response.status_code}")
        
        return created_groups
    
    def create_test_users(self, group_ids: Dict[str, str]):
        """Create 10 test users and assign them to different groups"""
        print("Creating test users...")
        
        # User assignments to groups for testing
        user_group_assignments = {
            "Test1": ["Developer"],
            "Test2": ["Tester"],
            "Test3": ["App_admin"],
            "Test4": ["Admin"],
            "Test5": ["Customer"],
            "Test6": ["Developer", "Basic"],
            "Test7": ["Tester", "Pro"],
            "Test8": ["Admin", "Pro+"],
            "Test9": ["Customer", "Basic"],
            "Test10": ["App_admin", "Pro"]
        }
        
        url = f"{self.base_url}/admin/realms/{self.realm}/users"
        
        for i in range(1, 11):
            username = f"Test{i}"
            user_data = {
                "username": username,
                "email": f"test{i}@nexus.com",
                "firstName": f"Test",
                "lastName": f"User{i}",
                "enabled": True,
                "emailVerified": True,
                "credentials": [{
                    "type": "password",
                    "value": "Test1234",
                    "temporary": False
                }]
            }
            
            response = requests.post(url, headers=self.get_headers(), json=user_data)
            if response.status_code == 201:
                print(f"✓ Created user: {username}")
                
                # Get user ID and assign to groups
                users_response = requests.get(url, headers=self.get_headers(), params={"username": username})
                if users_response.status_code == 200:
                    user = users_response.json()[0]
                    user_id = user["id"]
                    
                    # Assign to groups
                    for group_name in user_group_assignments.get(username, []):
                        group_id = group_ids.get(group_name)
                        if group_id:
                            group_url = f"{url}/{user_id}/groups/{group_id}"
                            group_response = requests.put(group_url, headers=self.get_headers())
                            if group_response.status_code == 204:
                                print(f"  ✓ Assigned {username} to group: {group_name}")
                            else:
                                print(f"  Failed to assign {username} to group {group_name}: {group_response.status_code}")
            else:
                print(f"Failed to create user {username}: {response.status_code} - {response.text}")
    
    def test_client_setup(self, client_secret: str):
        """Test the client setup by getting a JWT for a test user"""
        print("\nTesting client setup...")
        
        token_url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": "nexus-client",
            "client_secret": client_secret,
            "username": "Test1",
            "password": "Test1234"
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Successfully obtained JWT for Test1")
            print(f"✓ Access token length: {len(token_data['access_token'])}")
            return token_data['access_token']
        else:
            print(f"Failed to get JWT: {response.status_code} - {response.text}")
            return None

def main():
    keycloak_url = "http://localhost:8083"
    admin_username = "temp-admin"
    admin_password = "Test@1234"
    
    setup = KeycloakSetup(keycloak_url, admin_username, admin_password)
    
    print("Starting Keycloak development setup...")
    print("=" * 50)
    
    # Create client
    client_secret = setup.create_client()
    if not client_secret:
        print("Failed to create client. Exiting.")
        sys.exit(1)
    
    # Create groups
    group_ids = setup.create_groups()
    
    # Create users
    setup.create_test_users(group_ids)
    
    # Test setup
    jwt_token = setup.test_client_setup(client_secret)
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print(f"Client ID: nexus-client")
    print(f"Client Secret: {client_secret}")
    print("Test users: Test1-Test10 (password: Test1234)")
    
    if jwt_token:
        print(f"\nSample JWT for Test1 (first 50 chars): {jwt_token[:50]}...")
        
        print("\nYou can now test the Auth API with:")
        print(f"curl -X POST 'http://localhost:8083/realms/nexus/protocol/openid-connect/token' \\")
        print(f"  -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print(f"  -d 'grant_type=password&client_id=nexus-client&client_secret={client_secret}&username=Test1&password=Test1234'")

if __name__ == "__main__":
    main()
