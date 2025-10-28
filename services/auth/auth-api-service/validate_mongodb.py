import os
import subprocess
import requests

def get_jwt_token():
    # Activate venv and run get_keycloak_token.py
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    script_path = os.path.join(os.path.dirname(__file__), 'get_keycloak_token.py')
    result = subprocess.run([venv_python, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get JWT token:", result.stderr)
        return None
    return result.stdout.strip()

def validate_mongodb_service(jwt_token):
    # Replace with your actual orchestrator endpoint
    url = os.getenv('MONGODB_ORCHESTRATOR_URL', 'http://localhost:8000/example')
    payload = {"data": {"test": "value"}}
    headers = {"Authorization": f"Bearer {jwt_token}"}
    resp = requests.post(url, json=payload, headers=headers)
    print("Status:", resp.status_code)
    print("Response:", resp.text)

def main():
    jwt_token = get_jwt_token()
    if not jwt_token:
        return
    validate_mongodb_service(jwt_token)

if __name__ == "__main__":
    main()
