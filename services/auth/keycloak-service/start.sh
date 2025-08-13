#!/bin/bash

# Start Keycloak in the background
echo "Starting Keycloak server..."
/opt/keycloak/bin/kc.sh start-dev &
KEYCLOAK_PID=$!

# Wait for Keycloak to be ready
echo "Waiting for Keycloak to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:8080/health/ready > /dev/null 2>&1; then
        echo "Keycloak is ready!"
        break
    fi
    echo "Waiting... ($i/60)"
    sleep 2
done

# Configure the realm
echo "Configuring Keycloak realm..."
python3 /opt/keycloak/configure_realm.py

# Keep the container running
wait $KEYCLOAK_PID
