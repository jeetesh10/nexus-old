# Use the official Keycloak base image
FROM quay.io/keycloak/keycloak:21.1.2

# Set the working directory
WORKDIR /opt/keycloak

# Expose the HTTP port for the service to be accessible
EXPOSE 8080

# Start Keycloak in development mode
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start-dev"]
