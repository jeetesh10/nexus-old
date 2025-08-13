
Detailed Development Plan: Keycloak Microservice
This plan outlines the development, testing, and production migration activities for the Keycloak service, following the established Nexus Project architecture and project structure. The plan assumes the foundational platform infrastructure is complete and that the Keycloak service will be a core component of the platform, residing in a specific subdirectory within the project's repository structure.

Project and Microservice Structure
The Nexus project adheres to a multi-repository strategy within its GitHub organization1. The project structure organizes code into distinct logical units. The Keycloak service, being a core platform service, will reside in the 
services/core/ folder as per the updated structure2.
The high-level repository organization is as follows:
/your-github-organization-name
services/
core/
keycloak-service/ (Dedicated GitHub repo for the Keycloak authentication service) 3
product/
identity-resolution-service/ (Example product service)
shared-libraries/
platform-infra/
docs/
Each individual microservice repository, including 
keycloak-service, maintains a consistent internal folder structure to ensure clarity and maintainability4. This structure includes folders for source code, tests, and deployment manifests, along with a 
.devcontainer folder for GitHub Codespaces configuration5.
The project structure is organized to clearly separate core infrastructure services from business-facing product services.

File and Folder Structure

/nexus-dev02/ or /nexus/
├── .github/                                # GitHub Actions CI/CD workflows
├── .devcontainer/                          # Codespaces configuration
│
├── service/                                # Core platform services
│   ├── core/
│   │   ├── keycloak-service/               # Keycloak authentication service
│   │   └── data-access-service-api/        # Generic API for managed data stores
│
├── product/                                # Business-specific application services
│   ├── identity-resolution-service/        # Example product service
│   └── identity-graph-service/             # Another example product service
│
├── shared/                                 # Reusable libraries
│   └── python-client-for-infra-apis/
│
├── iac/                                    # Infrastructure as Code
│   ├── terraform/                          # Terraform files for all cloud resources
│   └── kubernetes/                         # K8s manifest files
│
└── docs/                                   # Project documentation


Keycloak Microservice Development Plan



Dev Activities (GitHub Codespaces)
Capability: Keycloak Service Core Functionality
Description: Develop and containerize the Keycloak service. This involves configuring Keycloak to run as a service, connecting it to its dedicated PostgreSQL database, and defining the initial realm, clients, and users required for the Nexus platform1.
Status: ⚪ Not Started

Task: Define Keycloak Configuration
Detailed Steps:
Create .env.example file: Create a .env.example file in the root of the keycloak-service repository with placeholders for DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, and other Keycloak-specific settings2.
Identify Environment Variables: Identify all required environment variables for a production-ready Keycloak container, including database connection details, realm configuration, and any security settings3.
Document Configuration: Document the purpose of each environment variable in the README.md file4.
Code: .env.example
Location: /nexus/services/core/keycloak-service/.env.example
# Keycloak Configuration - Example Environment Variables

# ==================================
# Database Configuration
# ==================================
# These variables configure the connection to the dedicated PostgreSQL database.
# In a production environment, these values will be managed by AWS Secrets Manager.
DB_VENDOR=postgres
DB_ADDR=__YOUR_DB_HOST__
DB_DATABASE=__YOUR_DB_NAME__
DB_USER=__YOUR_DB_USER__
DB_PASSWORD=__YOUR_DB_PASSWORD__

# ==================================
# Keycloak Admin Credentials
# ==================================
# Initial admin credentials for the Keycloak instance.
# These are used for the first-time setup and should be securely stored.
KEYCLOAK_ADMIN=__YOUR_ADMIN_USER__
KEYCLOAK_ADMIN_PASSWORD=__YOUR_ADMIN_PASSWORD__

# ==================================
# General Configuration
# ==================================
# This is the public URL of the Keycloak service. It's crucial for token issuance
# and redirects. Update with your specific domain.
KC_HOSTNAME_URL=https://auth.nexus.platform

# HTTP and HTTPS ports for Keycloak.
# In a containerized environment, these are typically exposed to a proxy.
KC_HTTP_PORT=8080
KC_HTTPS_PORT=8443

# The 'proxy' setting indicates that Keycloak is running behind a reverse proxy.
# 'edge' is a common setting for this.
KC_PROXY=edge

# Set to true to enable health check endpoints (e.g., /health/ready, /health/live).
KC_HEALTH_ENABLED=true

# Set to true to enable metrics endpoints (e.g., /metrics).
KC_METRICS_ENABLED=true

# Logging level for the Keycloak service.
# Options: ALL, DEBUG, INFO, WARN, ERROR, OFF.
KC_LOG_LEVEL=INFO

# ==================================
# Database Connection Pool
# ==================================
# Maximum number of connections in the database connection pool.
# Adjust based on expected load.
KC_DB_POOL_MAX_SIZE=50


Task: Create Dockerfile for Keycloak Service
Detailed Steps:
Select Base Image: Start with an official Keycloak base image from Docker Hub5.
Write Dockerfile: Write the Dockerfile to copy custom configuration files or scripts into the image6. Expose the required port (e.g., 8080) for the service to be accessible7. Ensure the 
Dockerfile adheres to best practices for container security and efficiency8.
Code: Dockerfile
Location: /nexus/services/core/keycloak-service/Dockerfile
# Use the official Keycloak base image
FROM quay.io/keycloak/keycloak:21.1.2

# Set the working directory
WORKDIR /opt/keycloak

# Expose the HTTP port for the service to be accessible
EXPOSE 8080

# The Keycloak server is started via the `start.sh` script, which will be added later.
# For now, we rely on the entrypoint from the base image.
# We will define a custom entrypoint/command later in the realm configuration task
# to run our custom scripts.
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start"]


Task: Configure Keycloak Realm and Clients
Detailed Steps:
Develop a Script: Develop a Python script to interact with the Keycloak Admin API or an equivalent tool to programmatically configure the realm9.
Define nexus-platform Realm: Define the nexus-platform realm with appropriate settings (e.g., token lifespan, SSL requirements)10.
Create Clients: Create a client for the API Gateway, configured with the correct redirect URIs and scopes11.
Create Test User: Create a test user for development and testing purposes12.
Code: configure_realm.py
Location: /nexus/services/core/keycloak-service/configure_realm.py
Python
import os
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakConnectionError, KeycloakAuthenticationError
import time

# Function to wait for Keycloak to be ready
def wait_for_keycloak(keycloak_admin):
    print("Waiting for Keycloak to be ready...")
    for _ in range(60):  # Wait for up to 60 seconds
        try:
            keycloak_admin.realms.find()
            print("Keycloak is ready.")
            return True
        except (KeycloakConnectionError, KeycloakAuthenticationError):
            time.sleep(1)
    print("Keycloak did not become ready in time.")
    return False

# Function to configure the realm, clients, and users
def configure_keycloak():
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=f"http://localhost:8080/",
            username=os.getenv("KEYCLOAK_ADMIN"),
            password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
            realm_name="master",
            verify=False
        )

        if not wait_for_keycloak(keycloak_admin):
            return

        # 1. Check if 'nexus-platform' realm exists, create if not
        realms = keycloak_admin.realms.find()
        realm_exists = any(r['realm'] == 'nexus-platform' for r in realms)

        if not realm_exists:
            print("Creating 'nexus-platform' realm...")
            keycloak_admin.realms.create_realm(payload={
                "realm": "nexus-platform",
                "enabled": True,
                "sslRequired": "external",
                "accessTokenLifespan": 300
            })
            print("'nexus-platform' realm created.")

        keycloak_admin.realm_name = "nexus-platform"

        # 2. Create client for API Gateway
        client_id = "nexus-api-gateway"
        clients = keycloak_admin.clients.find()
        client_exists = any(c['clientId'] == client_id for c in clients)

        if not client_exists:
            print(f"Creating client '{client_id}'...")
            keycloak_admin.clients.create(payload={
                "clientId": client_id,
                "name": "Nexus API Gateway",
                "enabled": True,
                "protocol": "openid-connect",
                "redirectUris": ["https://api.nexus.platform/*"],
                "publicClient": False,
                "authorizationServicesEnabled": True,
                "bearerOnly": False
            })
            print(f"Client '{client_id}' created.")

        # 3. Create a test user
        username = "test-user"
        users = keycloak_admin.users.find()
        user_exists = any(u['username'] == username for u in users)

        if not user_exists:
            print(f"Creating test user '{username}'...")
            keycloak_admin.users.create(payload={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "firstName": "Test",
                "lastName": "User",
                "credentials": [{
                    "type": "password",
                    "value": "TestPass123", # Placeholder password for dev/test
                    "temporary": False
                }]
            })
            print(f"Test user '{username}' created.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    configure_keycloak()


Task: Create a Manual Test Client (Login and Landing Page)
Detailed Steps:
Create HTML Files: Create two HTML files: login.html and landing.html. login.html will have a link to initiate the Keycloak login flow. landing.html will receive the user's information after a successful login.
Add JavaScript: Use JavaScript in login.html to redirect to the Keycloak login page. In landing.html, use JavaScript to parse the JWT from the URL, decode it, and display the user's information (e.g., username, groups).
Configure Keycloak Client: Create a new Keycloak client in the nexus-platform realm specifically for this manual test client. Set the redirectUris to include the URL of the landing.html page.
Test Manually:
Open login.html in a web browser.
Click the login link, which redirects you to the Keycloak login page.
Enter the credentials for the test user created in the previous step.
After successful authentication, you will be redirected to landing.html, where your user details and group information from the JWT should be displayed.
Code: login.html
Location: /nexus/services/core/keycloak-service/login.html
HTML
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Platform Login</title>
</head>
<body>
    <h1>Welcome to the Nexus Platform</h1>
    <p>Please log in to continue.</p>
    <button onclick="login()">Login</button>

    <script>
        function login() {
            // Replace with your Keycloak client configuration
            const clientId = 'manual-test-client';
            const redirectUri = 'http://localhost:8080/landing.html';
            const authUrl = `http://localhost:8080/realms/nexus-platform/protocol/openid-connect/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=token&scope=openid`;
            window.location.href = authUrl;
        }
    </script>
</body>
</html>

Code: landing.html
Location: /nexus/services/core/keycloak-service/landing.html
HTML
<!DOCTYPE html>
<html>
<head>
    <title>Landing Page</title>
</head>
<body>
    <h1>Welcome, <span id="username"></span>!</h1>
    <p>Your user details:</p>
    <pre id="user-info"></pre>
    <p>Your groups:</p>
    <pre id="user-groups"></pre>
    <a href="/">Logout</a>

    <script>
        function parseJwt(token) {
            try {
                const base64Url = token.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join(''));
                return JSON.parse(jsonPayload);
            } catch (e) {
                return null;
            }
        }

        window.onload = function() {
            const hash = window.location.hash.substr(1);
            const params = new URLSearchParams(hash);
            const accessToken = params.get('access_token');

            if (accessToken) {
                const decodedToken = parseJwt(accessToken);
                if (decodedToken) {
                    document.getElementById('username').innerText = decodedToken.preferred_username;
                    document.getElementById('user-info').innerText = JSON.stringify(decodedToken, null, 2);
                    // Assuming groups are in a 'groups' claim in the token
                    if (decodedToken.groups) {
                        document.getElementById('user-groups').innerText = JSON.stringify(decodedToken.groups, null, 2);
                    } else {
                        document.getElementById('user-groups').innerText = "No groups found.";
                    }
                } else {
                    document.getElementById('username').innerText = "Guest";
                    document.getElementById('user-info').innerText = "Error decoding token.";
                }
            } else {
                document.getElementById('username').innerText = "Guest";
                document.getElementById('user-info').innerText = "No access token found.";
            }
        };
    </script>
</body>
</html>


Task: Unit and Integration Testing
Detailed Steps:
Create Test Directories: Create tests/unit/ and tests/integration/ directories.
Write Unit Tests: Write unit tests to validate the configuration loading logic.
Write Integration Tests: Write integration tests that use a temporary Keycloak instance to verify client and user creation and token issuance.
Run Tests: Run all tests using pytest within the Codespace environment.
Code: tests/integration/test_keycloak_setup.py
Location: /nexus/services/core/keycloak-service/tests/integration/test_keycloak_setup.py
Python
import pytest
import os
from keycloak import KeycloakAdmin, KeycloakOpenID
from configure_realm import configure_keycloak
import subprocess
import time

@pytest.fixture(scope="session", autouse=True)
def run_keycloak_container():
    # Start a temporary Keycloak container for testing
    print("Starting Keycloak container for integration tests...")
    subprocess.run([
        "docker", "run", "-d",
        "--name", "test-keycloak",
        "-p", "8080:8080",
        "-e", f"KEYCLOAK_ADMIN={os.getenv('KEYCLOAK_ADMIN')}",
        "-e", f"KEYCLOAK_ADMIN_PASSWORD={os.getenv('KEYCLOAK_ADMIN_PASSWORD')}",
        "quay.io/keycloak/keycloak:21.1.2",
        "start-dev"
    ], check=True)

    # Wait for the Keycloak server to start
    time.sleep(10)

    try:
        yield
    finally:
        # Stop and remove the container
        print("Stopping Keycloak container...")
        subprocess.run(["docker", "stop", "test-keycloak"], check=True)
        subprocess.run(["docker", "rm", "test-keycloak"], check=True)

def test_realm_and_client_creation():
    # Run the realm configuration script
    configure_keycloak()

    # Verify realm and client exist
    keycloak_admin = KeycloakAdmin(
        server_url=f"http://localhost:8080/",
        username=os.getenv("KEYCLOAK_ADMIN"),
        password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
        realm_name="nexus-platform",
        verify=False
    )
    realm_info = keycloak_admin.realms.by_name("nexus-platform")
    assert realm_info is not None

    clients = keycloak_admin.clients.find()
    assert any(c['clientId'] == "nexus-api-gateway" for c in clients)

def test_user_creation_and_token_retrieval():
    # Run the realm configuration script
    configure_keycloak()

    # Verify user can get a token
    keycloak_openid = KeycloakOpenID(
        server_url=f"http://localhost:8080/",
        client_id="nexus-api-gateway",
        realm_name="nexus-platform",
        verify=False
    )

    token = keycloak_openid.token(
        username="test-user",
        password="TestPass123"
    )

    assert "access_token" in token


QA & Testing Activities (DigitalOcean QA Instance)
Capability: End-to-End & Performance Testing
Description: Deploy the Keycloak service to the DigitalOcean QA instance to perform comprehensive testing. This includes verifying secure communication, performance under load, and its integration with other simulated services.
Status: ⚪ Not Started

Task: Deploy Keycloak to DigitalOcean QA
Detailed Steps:
Push Docker Image: Push the finalized Docker image to a container registry13.
Apply Kubernetes Manifests: Apply the Kubernetes deployment and service manifests from the kubernetes/ directory to the QA cluster14.
Verify Pods: Verify that the Keycloak pod is running and healthy15.
Confirm Service Exposure: Confirm that the service is exposed internally and can be accessed by other services in the QA environment16.

Task: Integration Testing with a Mock Service
Detailed Steps:
Deploy Mock Service: Deploy a simple mock service to the QA cluster and configure it to use Keycloak for authentication17.
Obtain and Use Token: Make a request to Keycloak to get a token and then use that token to call the protected mock service endpoint18.
Validate Access: Validate that the mock service correctly grants access with a valid token and denies access with an invalid token19.

Task: Performance Testing
Detailed Steps:
Use Load Testing Tool: Use a load testing tool like Locust or JMeter to simulate concurrent users requesting tokens from Keycloak20.
Measure Metrics: Measure key metrics, including response times, latency, and error rates21.
Document Results: Document the results and recommendations in a test report22.

Production Activities (AWS vs. Google)
Capability: Production Migration
Description: Prepare and deploy the finalized Keycloak service to the production environment, ensuring all production-level security and reliability requirements are met.
Status: ⚪ Not Started

Task: Refine and Secure Production Manifests
Detailed Steps:
Update Manifests: Update the kubernetes/ manifests to specify production-level resource requests and limits (CPU, memory)23.
Configure Secrets Management: Configure secrets management to securely inject database credentials and other sensitive information from AWS Secrets Manager24.
Ensure Correct Service Type: Ensure the Service manifest uses the correct service type and internal DNS naming conventions for the production environment25.

Task: Implement CI/CD Pipeline
Detailed Steps:
Create Workflow File: Create a ci.yml file in the .github/workflows directory26.
Configure Build: Configure the workflow to automatically build the Docker image upon a new commit to the main branch27.
Run Tests: Run unit and integration tests within the pipeline28.
Push Image: Push the image to the production-ready nexus artifact repository29.
Trigger Deployment: Trigger a deployment to the AWS production EKS cluster30.

Task: Deploy to Production
Detailed Steps:
Execute Pipeline: Execute the CI/CD pipeline31.
Monitor Status: Monitor the deployment status to ensure the pods start and are healthy32.
Perform Smoke Test: Perform a final smoke test to verify basic functionality33.

