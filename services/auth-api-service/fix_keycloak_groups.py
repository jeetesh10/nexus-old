#!/usr/bin/env python3
"""
Fix Keycloak Groups in JWT
Add group mapper to nexus-client so groups are included in JWT tokens
"""

import requests
import json
import sys

class KeycloakGroupsFixer:
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
    
    def get_headers(self) -> dict:
        """Get headers with admin token"""
        if not self.admin_token:
            self.get_admin_token()
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def get_client_id(self) -> str:
        """Get the internal ID of the nexus-client"""
        url = f"{self.base_url}/admin/realms/{self.realm}/clients"
        response = requests.get(url, headers=self.get_headers(), params={"clientId": "nexus-client"})
        
        if response.status_code == 200:
            clients = response.json()
            if clients:
                return clients[0]["id"]
        
        print("Failed to find nexus-client")
        return None
    
    def add_groups_mapper(self, client_internal_id: str):
        """Add groups mapper to the client"""
        print("Adding groups mapper to nexus-client...")
        
        mapper_data = {
            "name": "groups",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-group-membership-mapper",
            "consentRequired": False,
            "config": {
                "full.path": "true",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "groups",
                "userinfo.token.claim": "true"
            }
        }
        
        url = f"{self.base_url}/admin/realms/{self.realm}/clients/{client_internal_id}/protocol-mappers/models"
        response = requests.post(url, headers=self.get_headers(), json=mapper_data)
        
        if response.status_code == 201:
            print("✓ Groups mapper added successfully")
            return True
        else:
            print(f"Failed to add groups mapper: {response.status_code} - {response.text}")
            return False
    
    def check_existing_mappers(self, client_internal_id: str):
        """Check if groups mapper already exists"""
        url = f"{self.base_url}/admin/realms/{self.realm}/clients/{client_internal_id}/protocol-mappers/models"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            mappers = response.json()
            for mapper in mappers:
                if mapper.get("name") == "groups":
                    print("✓ Groups mapper already exists")
                    return True
        
        return False
    
    def test_jwt_with_groups(self):
        """Test JWT generation to see if groups are now included"""
        print("\nTesting JWT with groups...")
        
        token_url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": "nexus-client",
            "client_secret": "Ooq6EKQ4lCaGVgrNMOMyzRXelWWHLeKM",
            "username": "Test1",
            "password": "Test1234"
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            
            # Decode JWT to check groups (basic decode without verification)
            import base64
            import json
            
            # Split JWT and get payload
            parts = access_token.split('.')
            if len(parts) >= 2:
                # Add padding if necessary
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                
                try:
                    decoded = base64.b64decode(payload)
                    jwt_payload = json.loads(decoded)
                    
                    print("✓ JWT generated successfully")
                    print(f"Username: {jwt_payload.get('preferred_username', 'N/A')}")
                    print(f"Groups: {jwt_payload.get('groups', 'No groups found')}")
                    
                    if 'groups' in jwt_payload and jwt_payload['groups']:
                        print("✅ Groups are now included in JWT!")
                        return True
                    else:
                        print("❌ Groups still not included in JWT")
                        return False
                        
                except Exception as e:
                    print(f"Error decoding JWT: {e}")
                    return False
        else:
            print(f"Failed to get JWT: {response.status_code} - {response.text}")
            return False
    
    def fix_groups(self):
        """Main method to fix groups in JWT"""
        print("Fixing Keycloak Groups in JWT...")
        print("=" * 50)
        
        # Get client internal ID
        client_internal_id = self.get_client_id()
        if not client_internal_id:
            return False
        
        print(f"Found nexus-client with ID: {client_internal_id}")
        
        # Check if mapper already exists
        if not self.check_existing_mappers(client_internal_id):
            # Add groups mapper
            if not self.add_groups_mapper(client_internal_id):
                return False
        
        # Test JWT
        return self.test_jwt_with_groups()

def main():
    keycloak_url = "http://localhost:8083"
    admin_username = "temp-admin"
    admin_password = "Test@1234"
    
    fixer = KeycloakGroupsFixer(keycloak_url, admin_username, admin_password)
    
    if fixer.fix_groups():
        print("\n" + "=" * 50)
        print("✅ Groups are now included in JWT tokens!")
        print("You can now test the Auth API with group-based authorization.")
    else:
        print("\n" + "=" * 50)
        print("❌ Failed to configure groups in JWT.")
        print("You may need to check the Keycloak admin console manually.")

if __name__ == "__main__":
    main()
