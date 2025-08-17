#!/usr/bin/env python3
"""
Upload Fixed Environment Files to Postman
Uploads the corrected environment files to Postman workspace
"""

import json
import requests
import sys
import os

class PostmanEnvironmentUploader:
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
    
    def upload_environments(self, environment_files, workspace_name="nexus"):
        """Upload environments to workspace"""
        print(f"🚀 Uploading environments to Postman workspace: '{workspace_name}'")
        
        # Find workspace
        workspace = self.find_workspace(workspace_name)
        if not workspace:
            print(f"❌ Workspace '{workspace_name}' not found!")
            return False
        
        workspace_id = workspace.get("id")
        print(f"✅ Found workspace: {workspace.get('name')} (ID: {workspace_id})")
        
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
        
        print("\n🎉 Environment upload completed!")
        return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python upload-environments.py <postman_api_key>")
        print("Example: python upload-environments.py PMAK-xxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)

    api_key = sys.argv[1]    # Validate API key format
    if not api_key.startswith("PMAK-"):
        print("❌ Invalid Postman API key format. Should start with 'PMAK-'")
        sys.exit(1)
    
    print("🔐 Postman API Key validated")
    
    # Initialize uploader
    uploader = PostmanEnvironmentUploader(api_key)
    
    # Define fixed environment files to upload
    environment_files = [
        "postman-collections/fixed_nexus_platform_development_environment.json",
        "postman-collections/fixed_nexus_platform_staging_environment.json",
        "postman-collections/fixed_nexus_platform_production_environment.json"
    ]
    
    # Upload to workspace
    success = uploader.upload_environments(environment_files, "nexus")
    
    if success:
        print("\n✅ All environments uploaded successfully to your Postman workspace!")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
