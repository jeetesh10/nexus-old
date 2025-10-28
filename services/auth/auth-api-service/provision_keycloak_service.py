import os
import requests
import sys

def get_admin_token():
    url = f"{os.getenv('KEYCLOAK_URL')}/realms/master/protocol/openid-connect/token"
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': os.getenv('KEYCLOAK_ADMIN', 'admin'),
        'password': os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin')
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()['access_token']

def create_client(realm, client_id, secret):
    token = get_admin_token()
    url = f"{os.getenv('KEYCLOAK_URL')}/admin/realms/{realm}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "clientId": client_id,
        "enabled": True,
        "directAccessGrantsEnabled": True,
        "publicClient": False,
        "secret": secret
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 201:
        print(f"Client '{client_id}' created successfully.")
    elif resp.status_code == 409:
        print(f"Client '{client_id}' already exists.")
    else:
        print(f"Error creating client: {resp.status_code} {resp.text}")

def create_user(realm, username, password):
    token = get_admin_token()
    url = f"{os.getenv('KEYCLOAK_URL')}/admin/realms/{realm}/users"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "username": username,
        "enabled": True,
        "credentials": [{"type": "password", "value": password, "temporary": False}]
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 201:
        print(f"User '{username}' created successfully.")
    elif resp.status_code == 409:
        print(f"User '{username}' already exists.")
    else:
        print(f"Error creating user: {resp.status_code} {resp.text}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python provision_keycloak_service.py <service_name>")
        sys.exit(1)
    service_name = sys.argv[1]
    realm = os.getenv('KEYCLOAK_REALM', 'nexus')
    client_id = f"{service_name}-client"
    user = f"{service_name}_user"
    secret = f"{service_name}_secret"
    password = f"{service_name}_pass"
    create_client(realm, client_id, secret)
    create_user(realm, user, password)
    print(f"Client ID: {client_id}\nClient Secret: {secret}\nUsername: {user}\nPassword: {password}")

if __name__ == "__main__":
    main()
