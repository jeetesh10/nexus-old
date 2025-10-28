#!/usr/bin/env python3
"""
Auth API Service for Nexus Platform
Provides authentication endpoints for other services
"""
import json
import logging
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Keycloak configuration from environment variables
keycloak_config = {
    'base_url': os.getenv('KEYCLOAK_BASE_URL', 'http://keycloak:8080'),
    'realm': os.getenv('KEYCLOAK_REALM', 'nexus-platform'),
    'client_id': os.getenv('KEYCLOAK_CLIENT_ID', 'nexus-platform'),
    'client_secret': os.getenv('KEYCLOAK_CLIENT_SECRET', ''),
    'admin_username': os.getenv('KEYCLOAK_ADMIN_USERNAME', ''),
    'admin_password': os.getenv('KEYCLOAK_ADMIN_PASSWORD', '')
}

# JWT configuration
jwt_config = {
    'issuer': f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}",
    'audience': 'nexus-platform',
    'jwks_url': f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}/protocol/openid-connect/certs"
}

@app.route('/api/auth/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        health_data = {
            "status": "healthy",
            "service": "auth-api",
            "version": "1.0.0"
        }
        return jsonify(health_data), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_data = {"status": "unhealthy", "error": str(e)}
        return jsonify(error_data), 500

@app.route('/api/auth/validate-token', methods=['GET'])
def validate_token():
    """Validate JWT token"""
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Decode token without verification first to get header
        unverified_header = jwt.get_unverified_header(token)
        
        # Get public key from Keycloak
        jwks_client = PyJWKClient(jwt_config['jwks_url'])
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            audience=jwt_config['audience'],
            issuer=jwt_config['issuer']
        )
        
        # Check if token is expired
        if 'exp' in payload and datetime.fromtimestamp(payload['exp']) < datetime.now():
            return jsonify({"error": "Token expired"}), 401
        
        response_data = {
            "valid": True,
            "user_id": payload.get('sub'),
            "username": payload.get('preferred_username'),
            "email": payload.get('email'),
            "exp": payload.get('exp'),
            "iat": payload.get('iat')
        }
        
        return jsonify(response_data), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 401
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 500

@app.route('/api/auth/user-info', methods=['GET'])
def get_user_info():
    """Get user information from token"""
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Validate token first
        unverified_header = jwt.get_unverified_header(token)
        jwks_client = PyJWKClient(jwt_config['jwks_url'])
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            audience=jwt_config['audience'],
            issuer=jwt_config['issuer']
        )
        
        user_info = {
            "user_id": payload.get('sub'),
            "username": payload.get('preferred_username'),
            "email": payload.get('email'),
            "name": payload.get('name'),
            "given_name": payload.get('given_name'),
            "family_name": payload.get('family_name'),
            "groups": payload.get('groups', []),
            "roles": payload.get('realm_access', {}).get('roles', [])
        }
        
        return jsonify(user_info), 200
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        return jsonify({"error": f"Failed to get user info: {str(e)}"}), 500

@app.route('/api/auth/user-groups', methods=['GET'])
def get_user_groups():
    """Get user groups from token"""
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Validate token first
        unverified_header = jwt.get_unverified_header(token)
        jwks_client = PyJWKClient(jwt_config['jwks_url'])
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            audience=jwt_config['audience'],
            issuer=jwt_config['issuer']
        )
        
        groups = payload.get('groups', [])
        
        return jsonify({"groups": groups}), 200
        
    except Exception as e:
        logger.error(f"Get user groups error: {e}")
        return jsonify({"error": f"Failed to get user groups: {str(e)}"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Login user with username and password"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Keycloak token endpoint
        token_url = f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'password',
            'client_id': keycloak_config['client_id'],
            'client_secret': keycloak_config['client_secret'],
            'username': username,
            'password': password
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            return jsonify(token_data), 200
        else:
            return jsonify({"error": "Login failed"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/api/auth/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400
        
        # Keycloak token refresh endpoint
        token_url = f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': keycloak_config['client_id'],
            'client_secret': keycloak_config['client_secret'],
            'refresh_token': refresh_token
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            return jsonify(token_data), 200
        else:
            return jsonify({"error": "Token refresh failed"}), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """Logout user"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Keycloak logout endpoint
        logout_url = f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}/protocol/openid-connect/logout"
        
        data = {
            'client_id': keycloak_config['client_id'],
            'client_secret': keycloak_config['client_secret'],
            'refresh_token': token
        }
        
        response = requests.post(logout_url, data=data, timeout=10)
        
        if response.status_code == 204:
            return jsonify({"message": "Logged out successfully"}), 200
        else:
            return jsonify({"error": "Logout failed"}), 400
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@app.route('/api/auth/openid-config', methods=['GET'])
def get_openid_config():
    """Get OpenID Connect configuration"""
    try:
        config_url = f"{keycloak_config['base_url']}/realms/{keycloak_config['realm']}/.well-known/openid_configuration"
        response = requests.get(config_url, timeout=10)
        
        if response.status_code == 200:
            config_data = response.json()
            return jsonify(config_data), 200
        else:
            return jsonify({"error": "Failed to get OpenID configuration"}), 500
            
    except Exception as e:
        logger.error(f"OpenID config error: {e}")
        return jsonify({"error": f"Failed to get OpenID configuration: {str(e)}"}), 500

if __name__ == '__main__':
    # Default to 8084 to align with gateway configuration
    port = int(os.getenv('PORT', 8084))
    logger.info(f"🔐 Auth API Service running on port {port}")
    logger.info(f"📊 Health check: http://localhost:{port}/api/auth/health")
    logger.info(f"🔑 Token validation: http://localhost:{port}/api/auth/validate-token")
    logger.info(f"👤 User info: http://localhost:{port}/api/auth/user-info")
    logger.info(f"👥 User groups: http://localhost:{port}/api/auth/user-groups")
    
    app.run(host='0.0.0.0', port=port, debug=False)
