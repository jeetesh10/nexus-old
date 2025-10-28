#!/usr/bin/env python3
"""
Upload Database Orchestrator Collections to Postman
"""

import requests
import json
import os

# Postman API Configuration
POSTMAN_API_KEY = os.getenv("POSTMAN_API_KEY", "your-postman-api-key-here")
WORKSPACE_NAME = "Nexus"
BASE_URL = "https://api.getpostman.com"

def get_workspace_id():
    """Get the workspace ID for the nexus workspace"""
    headers = {
        "X-API-Key": POSTMAN_API_KEY
    }
    
    response = requests.get(f"{BASE_URL}/workspaces", headers=headers)
    
    if response.status_code == 200:
        workspaces = response.json().get("workspaces", [])
        for workspace in workspaces:
            if workspace.get("name") == WORKSPACE_NAME:
                return workspace.get("id")
    
    print(f"❌ Workspace '{WORKSPACE_NAME}' not found")
    return None

def upload_collection(collection_file, workspace_id):
    """Upload a collection to Postman"""
    headers = {
        "X-API-Key": POSTMAN_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Read collection file
    with open(collection_file, 'r') as f:
        collection_data = json.load(f)
    
    # Prepare the request
    payload = {
        "collection": collection_data
    }
    
    response = requests.post(
        f"{BASE_URL}/collections",
        headers=headers,
        json=payload,
        params={"workspace": workspace_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        collection_name = result.get("collection", {}).get("info", {}).get("name", "Unknown")
        collection_id = result.get("collection", {}).get("id", "Unknown")
        print(f"✅ Uploaded collection: {collection_name} (ID: {collection_id})")
        return collection_id
    else:
        print(f"❌ Failed to upload {collection_file}: {response.status_code} - {response.text}")
        return None

def upload_environment(environment_file, workspace_id):
    """Upload an environment to Postman"""
    headers = {
        "X-API-Key": POSTMAN_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Read environment file
    with open(environment_file, 'r') as f:
        environment_data = json.load(f)
    
    # Prepare the request
    payload = {
        "environment": environment_data
    }
    
    response = requests.post(
        f"{BASE_URL}/environments",
        headers=headers,
        json=payload,
        params={"workspace": workspace_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        environment_name = result.get("environment", {}).get("name", "Unknown")
        environment_id = result.get("environment", {}).get("id", "Unknown")
        print(f"✅ Uploaded environment: {environment_name} (ID: {environment_id})")
        return environment_id
    else:
        print(f"❌ Failed to upload {environment_file}: {response.status_code} - {response.text}")
        return None

def main():
    """Upload all database collections and environment"""
    print("🚀 Uploading Database Orchestrator Collections to Postman...")
    
    # Get workspace ID
    workspace_id = get_workspace_id()
    if not workspace_id:
        return
    
    print(f"📁 Found workspace: {WORKSPACE_NAME} (ID: {workspace_id})")
    
    # Upload collections
    collections = [
        "postman-collections/nexus_mongodb_orchestrator_collection.json",
        "postman-collections/nexus_postgresql_orchestrator_collection.json"
    ]
    
    uploaded_collections = []
    for collection_file in collections:
        if os.path.exists(collection_file):
            collection_id = upload_collection(collection_file, workspace_id)
            if collection_id:
                uploaded_collections.append(collection_id)
        else:
            print(f"⚠️  Collection file not found: {collection_file}")
    
    # Upload environment
    environment_file = "postman-collections/nexus_database_environment.json"
    if os.path.exists(environment_file):
        environment_id = upload_environment(environment_file, workspace_id)
    else:
        print(f"⚠️  Environment file not found: {environment_file}")
    
    print(f"\n🎉 Upload complete!")
    print(f"📊 Uploaded {len(uploaded_collections)} collections to workspace '{WORKSPACE_NAME}'")
    print(f"🌐 Check your Postman workspace to see the new collections!")

if __name__ == "__main__":
    main()
