"""
Test Auth API Service
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import jwt as pyjwt
from fastapi.testclient import TestClient

# Import the app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, auth_service, config

client = TestClient(app)

# Test data
SAMPLE_JWT_PAYLOAD = {
    "sub": "test-user-id",
    "preferred_username": "test-user",
    "email": "test@example.com",
    "groups": [
        "Nexus/Employee/Admin",
        "Acmy/ID services/Role/Customer",
        "Acmy/ID services/Subscription/Pro+",
        "Acmy/MongoService/Role/Customer",
        "Acmy/MongoService/Subscription/Basic"
    ],
    "iss": "http://localhost:8080/realms/nexus-platform",
    "aud": "nexus-platform",
    "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    "iat": int(datetime.now(timezone.utc).timestamp())
}

SAMPLE_JWKS = {
    "keys": [
        {
            "kid": "test-key-id",
            "kty": "RSA",
            "use": "sig",
            "n": "test-modulus",
            "e": "AQAB"
        }
    ]
}

class TestAuthService:
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service_info"]["name"] == "auth-api-service"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Nexus Auth API Service"
    
    @patch.object(auth_service, 'validate_jwt')
    def test_validate_auth_success(self, mock_validate_jwt):
        """Test successful auth validation"""
        # Mock JWT validation
        mock_validate_jwt.return_value = SAMPLE_JWT_PAYLOAD
        
        request_data = {
            "jwt_token": "mock-jwt-token",
            "resource": "id-service",
            "client_context": "acmy",
            "action": "read"
        }
        
        response = client.post("/api/auth/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert data["allowed"] is True
        assert data["permissions"]["role"] == "customer"
        assert data["permissions"]["subscription"] == "pro+"
        assert data["user_context"]["email"] == "test@example.com"
    
    @patch.object(auth_service, 'validate_jwt')
    def test_validate_auth_invalid_token(self, mock_validate_jwt):
        """Test validation with invalid token"""
        # Mock JWT validation failure
        mock_validate_jwt.side_effect = ValueError("Invalid token")
        
        request_data = {
            "jwt_token": "invalid-token",
            "resource": "id-service", 
            "client_context": "acmy",
            "action": "read"
        }
        
        response = client.post("/api/auth/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert data["allowed"] is False
        assert "Invalid token" in data["error"]
    
    def test_parse_groups_acmy_customer(self):
        """Test group parsing for Acmy customer"""
        groups = [
            "Acmy/ID services/Role/Customer", 
            "Acmy/ID services/Subscription/Pro+"
        ]
        
        permissions = auth_service.parse_groups(groups, "acmy", "id-service")
        
        assert permissions.has_access is True
        assert permissions.role == "customer"
        assert permissions.subscription == "pro+"
        assert "bulk-operations" in permissions.features
        assert "webhooks" in permissions.features
    
    def test_parse_groups_nexus_admin(self):
        """Test group parsing for Nexus admin"""
        groups = ["Nexus/Employee/Admin"]
        
        permissions = auth_service.parse_groups(groups, "nexus", "id-service")
        
        assert permissions.has_access is True
        # Should have access even without specific service groups due to Nexus access
    
    def test_parse_groups_no_access(self):
        """Test group parsing with no relevant groups"""
        groups = ["SomeOther/Service/Role/User"]
        
        permissions = auth_service.parse_groups(groups, "acmy", "id-service")
        
        assert permissions.has_access is False
        assert permissions.role is None
        assert permissions.subscription is None
    
    def test_extract_role(self):
        """Test role extraction from groups"""
        groups = ["Acmy/ID services/Role/Admin", "Other/Group"]
        role = auth_service._extract_role(groups)
        assert role == "admin"
    
    def test_extract_subscription(self):
        """Test subscription extraction from groups"""
        groups = ["Acmy/ID services/Subscription/Pro+", "Other/Group"]
        subscription = auth_service._extract_subscription(groups)
        assert subscription == "pro+"
    
    def test_get_features_admin_pro_plus(self):
        """Test feature calculation for admin with Pro+ subscription"""
        features = auth_service._get_features("admin", "pro+")
        
        expected_features = [
            "admin-access", "user-management", "full-control",
            "bulk-operations", "webhooks", "priority-support", "advanced-analytics"
        ]
        
        for feature in expected_features:
            assert feature in features
    
    def test_get_features_customer_basic(self):
        """Test feature calculation for customer with basic subscription"""
        features = auth_service._get_features("customer", "basic")
        
        expected_features = ["basic-access", "read-operations", "standard-operations", "basic-support"]
        
        for feature in expected_features:
            assert feature in features
    
    def test_check_action_permission_read(self):
        """Test read action permission"""
        permissions = auth_service.parse_groups(
            ["Acmy/ID services/Role/Customer", "Acmy/ID services/Subscription/Basic"],
            "acmy", "id-service"
        )
        
        assert auth_service.check_action_permission(permissions, "read") is True
    
    def test_check_action_permission_write_denied(self):
        """Test write action permission denied for customer"""
        permissions = auth_service.parse_groups(
            ["Acmy/ID services/Role/Customer", "Acmy/ID services/Subscription/Basic"],
            "acmy", "id-service"
        )
        
        assert auth_service.check_action_permission(permissions, "write") is False
    
    def test_check_action_permission_write_allowed(self):
        """Test write action permission allowed for admin"""
        permissions = auth_service.parse_groups(
            ["Acmy/ID services/Role/Admin", "Acmy/ID services/Subscription/Pro+"],
            "acmy", "id-service"
        )
        
        assert auth_service.check_action_permission(permissions, "write") is True

class TestGroupParsing:
    """Comprehensive tests for group parsing logic"""
    
    def test_case_insensitive_matching(self):
        """Test that group matching is case insensitive"""
        groups = ["acmy/id-service/role/customer", "acmy/id-service/subscription/pro"]
        permissions = auth_service.parse_groups(groups, "Acmy", "ID-Service")
        
        assert permissions.has_access is True
    
    def test_service_name_variations(self):
        """Test different service name formats"""
        test_cases = [
            (["Acmy/ID services/Role/Customer"], "acmy", "id-service"),
            (["Acmy/ID Service/Role/Customer"], "acmy", "id-service"),
            (["Acmy/id-service/Role/Customer"], "acmy", "id-service"),
        ]
        
        for groups, client, service in test_cases:
            permissions = auth_service.parse_groups(groups, client, service)
            assert permissions.has_access is True, f"Failed for groups: {groups}"
    
    def test_multiple_client_contexts(self):
        """Test user with access to multiple clients"""
        groups = [
            "Acmy/ID services/Role/Customer",
            "Acmy/ID services/Subscription/Pro+", 
            "Macy/ID services/Role/Admin",
            "Macy/ID services/Subscription/Basic"
        ]
        
        # Test Acmy context
        acmy_permissions = auth_service.parse_groups(groups, "acmy", "id-service")
        assert acmy_permissions.role == "customer"
        assert acmy_permissions.subscription == "pro+"
        
        # Test Macy context  
        macy_permissions = auth_service.parse_groups(groups, "macy", "id-service")
        assert macy_permissions.role == "admin"
        assert macy_permissions.subscription == "basic"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
