

import os
import requests
import sys
import argparse

def get_token(
    keycloak_url: str,
    realm: str,
    client_id: str,
    client_secret: str,
    username: str,
    password: str
):
    url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    data = {
        'grant_type': 'password',
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password
    }
    resp = requests.post(url, data=data)
    if resp.status_code == 200:
        print(resp.json()['access_token'])
    else:
        print(f"Error: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Get a Keycloak access token for a given client/user.")
    parser.add_argument('--keycloak-url', default=os.getenv('KEYCLOAK_URL', 'http://localhost:8080'))
    parser.add_argument('--realm', default=os.getenv('KEYCLOAK_REALM', 'nexus'))
    parser.add_argument('--client-id', default=os.getenv('KEYCLOAK_CLIENT_ID', 'mongodb-orchestrator'))
    parser.add_argument('--client-secret', default=os.getenv('KEYCLOAK_CLIENT_SECRET', 'changeme'))
    parser.add_argument('--username', default=os.getenv('KEYCLOAK_USERNAME', 'testuser'))
    parser.add_argument('--password', default=os.getenv('KEYCLOAK_PASSWORD', 'testpass'))
    args = parser.parse_args()
    get_token(
        keycloak_url=args.keycloak_url,
        realm=args.realm,
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password
    )

if __name__ == "__main__":
    main()
