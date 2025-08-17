#!/usr/bin/env python3
"""
Test script for Auth API service
Tests all endpoints with real JWTs from Keycloak
"""

import requests
import json
import sys

class AuthAPITester:
    def __init__(self):
        self.keycloak_url = "http://localhost:8083"
        self.auth_api_url = "http://localhost:8085"
        self.realm = "nexus"
        self.client_id = "nexus-client"
        self.client_secret = "Ooq6EKQ4lCaGVgrNMOMyzRXelWWHLeKM"
        
    def get_jwt(self, username: str, password: str) -> str:
        """Get JWT token for a user"""
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Failed to get JWT for {username}: {response.status_code} - {response.text}")
            return None
    
    def test_health(self):
        """Test health endpoint"""
        print("Testing /api/auth/health...")
        response = requests.get(f"{self.auth_api_url}/api/auth/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    
    def test_login(self, username: str, password: str):
        """Test login endpoint"""
        print(f"Testing /api/auth/login with {username}...")
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(f"{self.auth_api_url}/api/auth/login", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.json().get("access_token") if response.status_code == 200 else None
    
    def test_validate(self, token: str):
        """Test token validation endpoint"""
        print("Testing /api/auth/validate...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "jwt_token": token,
            "resource": "id-service",
            "client_context": "nexus",
            "action": "read"
        }
        response = requests.post(f"{self.auth_api_url}/api/auth/validate", headers=headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    
    def test_users(self, token: str):
        """Test users endpoint"""
        print("Testing /api/auth/users...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{self.auth_api_url}/api/auth/users", headers=headers, json={})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    
    def test_groups(self, token: str):
        """Test groups endpoint"""
        print("Testing /api/auth/groups...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{self.auth_api_url}/api/auth/groups", headers=headers, json={})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    
    def test_user_groups(self, token: str, username: str):
        """Test user groups endpoint"""
        print(f"Testing /api/auth/user-groups for {username}...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {"username": username}
        response = requests.post(f"{self.auth_api_url}/api/auth/user-groups", headers=headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("Auth API Service Test Suite")
        print("=" * 60)
        
        # Test health (no auth required)
        self.test_health()
        
        # Test login and get token
        token = self.test_login("Test1", "Test1234")
        
        if token:
            # Test validation
            self.test_validate(token)
            
            # Test users
            self.test_users(token)
            
            # Test groups
            self.test_groups(token)
            
            # Test user groups
            self.test_user_groups(token, "Test1")
            
            print("=" * 60)
            print("All tests completed!")
            print(f"JWT Token for Test1 (first 50 chars): {token[:50]}...")
            print("\nYou can use this token in Swagger UI or other API testing tools")
        else:
            print("Failed to get token, skipping authenticated tests")

if __name__ == "__main__":
    tester = AuthAPITester()
    tester.run_all_tests()
