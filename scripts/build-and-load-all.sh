#!/bin/bash
  # (removed stray line)
IMAGES=(
  "nexus/api-gateway:latest:services/api-gateway/gateway-service"
  "nexus/admin-dashboard:latest:services/admin-dashboard-service"
  "keycloak-service:latest:services/auth/keycloak-service"
  "nexus/auth-api:latest:services/auth/auth-api-service"
  "nexus/group-management:latest:services/access-control/group-management-service"
  "nexus/access-control:latest:services/access-control/access-control-service"
  "nexus/postgresql-orchestrator:latest:services/database/postgresql-orchestrator"
  "nexus/mongodb-orchestrator:latest:services/database/mongodb-orchestrator"
  "nexus/service-mesh:latest:services/service-mesh"
  "nexus/landing-page:latest:services/access-control/landing-page"

  "nexus/redis-orchestrator:latest:services/database/redis-orchestrator"
  "nexus/customer-portal:latest:services/customer-portal"
  "nexus/smartcart-bot:latest:services/smartcart-bot"
)


for entry in "${IMAGES[@]}"; do
  IFS=':' read -r image tag context <<< "$entry"
  image_tag="$image:$tag"
  echo "DEBUG: entry='$entry'"
  echo "DEBUG: image='$image' tag='$tag' context='$context'"
  echo -e "\n==== Building $image_tag from $context/Dockerfile ===="
  docker build -t "$image_tag" "$context"
  echo "==== Loading $image_tag into kind:nexus ===="
  kind load docker-image "$image_tag" --name nexus
  echo "==== Done: $image_tag ===="
done

echo -e "\nAll images built and loaded into kind cluster 'nexus'."
