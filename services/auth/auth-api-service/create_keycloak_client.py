import os
import requests

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

def create_client(realm, client_id, secret=None):
    token = get_admin_token()
    url = f"{os.getenv('KEYCLOAK_URL')}/admin/realms/{realm}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "clientId": client_id,
        "enabled": True,
        "directAccessGrantsEnabled": True,
        "publicClient": False,
        "secret": secret or "changeme"
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 201:
        print(f"Client '{client_id}' created successfully.")
    elif resp.status_code == 409:
        print(f"Client '{client_id}' already exists.")
    else:
        print(f"Error creating client: {resp.status_code} {resp.text}")

def main():
    realm = os.getenv('KEYCLOAK_REALM', 'nexus')
    client_id = os.getenv('KEYCLOAK_CLIENT_ID', 'service-client')
    secret = os.getenv('KEYCLOAK_CLIENT_SECRET', 'changeme')
    create_client(realm, client_id, secret)

if __name__ == "__main__":
    main()
