import yaml
import os

# The single source of truth
CONFIGMAP_PATH = 'iac/kubernetes/base/configmap.yaml'

# Mapping of ConfigMap keys to the service directories
SERVICE_MAP = {
    'API_GATEWAY_PORT': 'services/api-gateway',
    'ACCESS_CONTROL_PORT': 'services/access-control',
    'ADMIN_DASHBOARD_PORT': 'services/admin-dashboard',
    'LANDING_PAGE_PORT': 'services/landing-page',
    'AUTH_API_PORT': 'services/auth-api',
    'GROUP_MANAGEMENT_PORT': 'services/group-management'
}

def main():
    print("🔄 Synchronizing .env files from ConfigMap...")

    try:
        with open(CONFIGMAP_PATH, 'r') as f:
            configmap = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Error: ConfigMap not found at {CONFIGMAP_PATH}")
        return

    config_data = configmap.get('data', {})

    for key, service_dir in SERVICE_MAP.items():
        port = config_data.get(key)
        if not port:
            print(f"⚠️ Warning: Key '{key}' not found in ConfigMap. Skipping {service_dir}.")
            continue

        # Ensure the service directory exists
        if not os.path.exists(service_dir):
            print(f"ℹ️ Note: Service directory not found, creating: {service_dir}")
            os.makedirs(service_dir)
        
        env_path = os.path.join(service_dir, '.env')
        with open(env_path, 'w') as f:
            f.write(f"PORT={port}\n")
        print(f"✅ Wrote .env for {service_dir}")

    print("✨ Sync complete.")

if __name__ == "__main__":
    main()