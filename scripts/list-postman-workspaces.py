#!/usr/bin/env python3
"""
List available Postman workspaces
"""

import requests
import os

# Postman API Configuration
POSTMAN_API_KEY = os.getenv("POSTMAN_API_KEY", "your-postman-api-key-here")
BASE_URL = "https://api.getpostman.com"

def list_workspaces():
    """List all available workspaces"""
    headers = {
        "X-API-Key": POSTMAN_API_KEY
    }
    
    response = requests.get(f"{BASE_URL}/workspaces", headers=headers)
    
    if response.status_code == 200:
        workspaces = response.json().get("workspaces", [])
        print("📁 Available Postman Workspaces:")
        print("=" * 50)
        
        for workspace in workspaces:
            workspace_id = workspace.get("id", "Unknown")
            workspace_name = workspace.get("name", "Unknown")
            workspace_type = workspace.get("type", "Unknown")
            print(f"🏢 Name: {workspace_name}")
            print(f"   ID: {workspace_id}")
            print(f"   Type: {workspace_type}")
            print("-" * 30)
        
        return workspaces
    else:
        print(f"❌ Failed to get workspaces: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    list_workspaces()
