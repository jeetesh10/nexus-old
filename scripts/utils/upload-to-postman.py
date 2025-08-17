#!/usr/bin/env python3
"""
Postman Collection Uploader for Nexus Platform
Uploads generated collections to Postman workspace using Postman API
"""

import json
import requests
import sys
import os
from datetime import datetime

class PostmanUploader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.getpostman.com"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_workspaces(self):
        """Get list of workspaces"""
        try:
            response = requests.get(f"{self.base_url}/workspaces", headers=self.headers)
            response.raise_for_status()
            return response.json().get("workspaces", [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting workspaces: {e}")
            return []
    
    def find_workspace(self, workspace_name):
        """Find workspace by name"""
        workspaces = self.get_workspaces()
        for workspace in workspaces:
            if workspace.get("name", "").lower() == workspace_name.lower():
                return workspace
        return None
    
    def create_collection(self, workspace_id, collection_data):
        """Create collection in workspace"""
        try:
            # Prepare collection data for API
            collection_payload = {
                "collection": collection_data
            }
            
            response = requests.post(
                f"{self.base_url}/collections",
                headers=self.headers,
                json=collection_payload,
                params={"workspace": workspace_id}
            )
            response.raise_for_status()
            
            result = response.json()
            collection_id = result.get("collection", {}).get("uid")
            collection_name = result.get("collection", {}).get("name")
            
            print(f"✅ Collection '{collection_name}' created successfully!")
            print(f"   Collection ID: {collection_id}")
            print(f"   View URL: https://go.postman.co/collection/{collection_id}")
            
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating collection: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            return None
    
    def create_environment(self, workspace_id, environment_data):
        """Create environment in workspace"""
        try:
            response = requests.post(
                f"{self.base_url}/environments",
                headers=self.headers,
                json=environment_data,
                params={"workspace": workspace_id}
            )
            response.raise_for_status()
            
            result = response.json()
            environment_id = result.get("environment", {}).get("uid")
            environment_name = result.get("environment", {}).get("name")
            
            print(f"✅ Environment '{environment_name}' created successfully!")
            print(f"   Environment ID: {environment_id}")
            
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating environment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            return None
    
    def upload_collection_and_environments(self, collection_file, environment_files, workspace_name="nexus"):
        """Upload collection and environments to workspace"""
        print(f"🚀 Uploading to Postman workspace: '{workspace_name}'")
        
        # Find workspace
        workspace = self.find_workspace(workspace_name)
        if not workspace:
            print(f"❌ Workspace '{workspace_name}' not found!")
            print("Available workspaces:")
            workspaces = self.get_workspaces()
            for ws in workspaces:
                print(f"   - {ws.get('name', 'Unknown')}")
            return False
        
        workspace_id = workspace.get("id")
        print(f"✅ Found workspace: {workspace.get('name')} (ID: {workspace_id})")
        
        # Load and upload collection
        if os.path.exists(collection_file):
            print(f"📄 Loading collection from: {collection_file}")
            try:
                with open(collection_file, 'r', encoding='utf-8') as f:
                    collection_data = json.load(f)
                
                # Update collection info
                collection_data["info"]["name"] = "Nexus Platform Auth API"
                collection_data["info"]["description"] = "Complete API collection for Nexus Platform Auth Service with automated tests and authentication handling."
                collection_data["info"]["updatedAt"] = datetime.now().isoformat()
                
                result = self.create_collection(workspace_id, collection_data)
                if not result:
                    return False
                
            except Exception as e:
                print(f"❌ Error loading collection file: {e}")
                return False
        else:
            print(f"❌ Collection file not found: {collection_file}")
            return False
        
        # Upload environments
        for env_file in environment_files:
            if os.path.exists(env_file):
                print(f"📄 Loading environment from: {env_file}")
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        environment_data = json.load(f)
                    
                    result = self.create_environment(workspace_id, environment_data)
                    if not result:
                        print(f"⚠️  Failed to create environment from {env_file}")
                
                except Exception as e:
                    print(f"❌ Error loading environment file {env_file}: {e}")
            else:
                print(f"⚠️  Environment file not found: {env_file}")
        
        print("\n🎉 Upload completed successfully!")
        print(f"📋 Next Steps:")
        print(f"   1. Open Postman and go to your '{workspace_name}' workspace")
        print(f"   2. You'll see the 'Nexus Platform Auth API' collection")
        print(f"   3. Import the environments for different stages")
        print(f"   4. Start testing the APIs!")
        
        return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python upload-to-postman.py <postman_api_key>")
        print("Example: python upload-to-postman.py PMAK-xxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    # Validate API key format
    if not api_key.startswith("PMAK-"):
        print("❌ Invalid Postman API key format. Should start with 'PMAK-'")
        sys.exit(1)
    
    print("🔐 Postman API Key validated")
    
    # Initialize uploader
    uploader = PostmanUploader(api_key)
    
    # Define files to upload
    collection_file = "postman-collections/nexus_platform_auth_api_postman_collection.json"
    environment_files = [
        "postman-collections/nexus_platform_development_environment.json",
        "postman-collections/nexus_platform_staging_environment.json",
        "postman-collections/nexus_platform_production_environment.json"
    ]
    
    # Upload to workspace
    success = uploader.upload_collection_and_environments(
        collection_file, 
        environment_files, 
        "nexus"
    )
    
    if success:
        print("\n✅ All files uploaded successfully to your Postman workspace!")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
