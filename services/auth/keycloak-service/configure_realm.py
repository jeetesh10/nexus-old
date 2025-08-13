import os
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakConnectionError, KeycloakAuthenticationError
import time

# Function to wait for Keycloak to be ready
def wait_for_keycloak(keycloak_admin):
    print("Waiting for Keycloak to be ready...")
    for _ in range(60):  # Wait for up to 60 seconds
        try:
            keycloak_admin.get_realms()
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
            username=os.getenv("KEYCLOAK_ADMIN", "admin"),
            password=os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin"),
            realm_name="master",
            verify=False
        )

        if not wait_for_keycloak(keycloak_admin):
            return

        # 1. Check if 'nexus-platform' realm exists, create if not
        try:
            realms = keycloak_admin.get_realms()
            realm_exists = any(r['realm'] == 'nexus-platform' for r in realms)
        except Exception as e:
            print(f"Error checking realms: {e}")
            realm_exists = False

        if not realm_exists:
            print("Creating 'nexus-platform' realm...")
            keycloak_admin.create_realm(payload={
                "realm": "nexus-platform",
                "enabled": True,
                "sslRequired": "external",
                "accessTokenLifespan": 300
            })
            print("'nexus-platform' realm created.")

        # Switch to nexus-platform realm
        keycloak_admin.realm_name = "nexus-platform"

        # 2. Create client for API Gateway
        client_id = "nexus-api-gateway"
        try:
            clients = keycloak_admin.get_clients()
            client_exists = any(c['clientId'] == client_id for c in clients)
        except:
            client_exists = False

        if not client_exists:
            print(f"Creating client '{client_id}'...")
            keycloak_admin.create_client(payload={
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

        # 3. Create client for Admin Dashboard
        admin_client_id = "nexus-admin-dashboard"
        admin_client_exists = any(c['clientId'] == admin_client_id for c in clients)

        if not admin_client_exists:
            print(f"Creating client '{admin_client_id}'...")
            keycloak_admin.create_client(payload={
                "clientId": admin_client_id,
                "name": "Nexus Admin Dashboard",
                "enabled": True,
                "protocol": "openid-connect",
                "redirectUris": ["http://localhost:8081/*", "https://admin.nexus.platform/*"],
                "publicClient": True,
                "authorizationServicesEnabled": True,
                "bearerOnly": False
            })
            print(f"Client '{admin_client_id}' created.")

        # 4. Create client for Landing Page
        landing_client_id = "nexus-landing-page"
        landing_client_exists = any(c['clientId'] == landing_client_id for c in clients)

        if not landing_client_exists:
            print(f"Creating client '{landing_client_id}'...")
            keycloak_admin.create_client(payload={
                "clientId": landing_client_id,
                "name": "Nexus Landing Page",
                "enabled": True,
                "protocol": "openid-connect",
                "redirectUris": ["http://localhost:8082/*", "https://landing.nexus.platform/*"],
                "publicClient": True,
                "authorizationServicesEnabled": True,
                "bearerOnly": False
            })
            print(f"Client '{landing_client_id}' created.")

        # 5. Create groups for role-based access
        try:
            groups = keycloak_admin.get_groups()
        except:
            groups = []
        
        # Platform Admin group
        platform_admin_exists = any(g['name'] == 'platform-admin' for g in groups)
        if not platform_admin_exists:
            print("Creating 'platform-admin' group...")
            keycloak_admin.create_group(payload={
                "name": "platform-admin"
            })
            print("'platform-admin' group created.")

        # Service Admin group
        service_admin_exists = any(g['name'] == 'service-admin' for g in groups)
        if not service_admin_exists:
            print("Creating 'service-admin' group...")
            keycloak_admin.create_group(payload={
                "name": "service-admin"
            })
            print("'service-admin' group created.")

        # Product groups
        product_groups = ['admin-dashboard', 'id-service', 'parking-service']
        for product in product_groups:
            product_exists = any(g['name'] == product for g in groups)
            if not product_exists:
                print(f"Creating '{product}' group...")
                keycloak_admin.create_group(payload={
                    "name": product
                })
                print(f"'{product}' group created.")

        # 6. Create a test user
        username = "test-user"
        try:
            users = keycloak_admin.get_users()
            user_exists = any(u['username'] == username for u in users)
        except:
            user_exists = False

        if not user_exists:
            print(f"Creating test user '{username}'...")
            user_id = keycloak_admin.create_user(payload={
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
            
            # Add user to groups
            try:
                platform_admin_group = next(g for g in groups if g['name'] == 'platform-admin')
                keycloak_admin.group_user_add(user_id=user_id, group_id=platform_admin_group['id'])
            except:
                pass
            print(f"Test user '{username}' created and added to platform-admin group.")

        # 7. Create admin user
        admin_username = "admin"
        admin_exists = any(u['username'] == admin_username for u in users)

        if not admin_exists:
            print(f"Creating admin user '{admin_username}'...")
            admin_id = keycloak_admin.create_user(payload={
                "username": admin_username,
                "enabled": True,
                "emailVerified": True,
                "firstName": "Platform",
                "lastName": "Admin",
                "credentials": [{
                    "type": "password",
                    "value": "AdminPass123", # Placeholder password for dev/test
                    "temporary": False
                }]
            })
            
            # Add admin to platform-admin group
            try:
                platform_admin_group = next(g for g in groups if g['name'] == 'platform-admin')
                keycloak_admin.group_user_add(user_id=admin_id, group_id=platform_admin_group['id'])
            except:
                pass
            print(f"Admin user '{admin_username}' created and added to platform-admin group.")

        print("Keycloak configuration completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    configure_keycloak()
