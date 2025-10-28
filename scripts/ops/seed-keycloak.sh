#!/usr/bin/env bash
set -euo pipefail

# Seed Keycloak with realm, clients, groups, users for Nexus demo RBAC
# Requires: Docker Keycloak running locally on :8080 (scripts/start-platform.sh starts one)

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM="${KEYCLOAK_REALM:-nexus}"

# Clients
ADMIN_CLIENT_ID="admin-dashboard"
CUSTOMER_CLIENT_ID="customer-portal"
LANDING_CLIENT_ID="nexus-landing"
GATEWAY_CLIENT_ID="nexus-gateway"

# Resolve Codespaces host/origin for redirect URIs (optional)
# Priority: CODESPACES_HOST env -> derive from CODESPACE_NAME + GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN
LANDING_PORT="${LANDING_PORT:-8082}"
CODESPACES_HOST="${CODESPACES_HOST:-}"
if [[ -z "${CODESPACES_HOST}" && -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  CODESPACES_HOST="${CODESPACE_NAME}-${LANDING_PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
fi
CODESPACES_URL=""
if [[ -n "${CODESPACES_HOST}" ]]; then
  CODESPACES_URL="https://${CODESPACES_HOST}"
fi

# Allow user-provided additional redirect URIs and web origins (comma-separated)
EXTRA_REDIRECT_URIS="${EXTRA_REDIRECT_URIS:-}"
EXTRA_WEB_ORIGINS="${EXTRA_WEB_ORIGINS:-}"

build_json_array() {
  # Usage: build_json_array "item1,item2,item3" -> "\"item1\",\"item2\",\"item3\""
  local csv="$1"
  local result=""
  if [[ -n "$csv" ]]; then
    IFS=',' read -ra items <<< "$csv"
    for it in "${items[@]}"; do
      it_trimmed="${it## }"; it_trimmed="${it_trimmed%% }"
      if [[ -n "$it_trimmed" ]]; then
        if [[ -n "$result" ]]; then result+=","; fi
        result+="\"$it_trimmed\""
      fi
    done
  fi
  echo -n "$result"
}

EXTRA_REDIRECT_JSON=$(build_json_array "$EXTRA_REDIRECT_URIS")
EXTRA_ORIGINS_JSON=$(build_json_array "$EXTRA_WEB_ORIGINS")

# Groups
GROUP_ADMIN="platform-admins"
GROUP_CUSTOMER="customers"

# Users
ADMIN_USER_ID="tony-admin"
ADMIN_USER_EMAIL="tony.admin@example.com"
ADMIN_USER_PASS="changeme123"

CUSTOMER_USER_ID="tony-customer"
CUSTOMER_USER_EMAIL="tony.customer@example.com"
CUSTOMER_USER_PASS="changeme123"

# OIDC group membership mapper payload (used for gateway and public clients)
MAPPER_PAYLOAD='{"name":"groups","protocol":"openid-connect","protocolMapper":"oidc-group-membership-mapper","config":{"full.path":"false","claim.name":"groups","access.token.claim":"true","id.token.claim":"true"}}'

echo "Fetching admin access token..."
ACCESS_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d 'grant_type=password' \
  -d 'client_id=admin-cli' | jq -r .access_token)

if [[ -z "$ACCESS_TOKEN" || "$ACCESS_TOKEN" == "null" ]]; then
  echo "Failed to fetch admin token. Is Keycloak running at $KEYCLOAK_URL?" >&2
  exit 1
fi

kc() {
  local method="$1"; shift
  local path="$1"; shift
  curl -s -o /dev/null -w "%{http_code}" -X "$method" "$KEYCLOAK_URL$path" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H 'Content-Type: application/json' \
    "$@"
}

get() {
  curl -s -X GET "$KEYCLOAK_URL$1" -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json'
}

echo "Creating realm '$REALM' if not exists..."
if [[ "$(kc GET /admin/realms/$REALM)" == "200" ]]; then
  echo "Realm exists."
else
  http=$(kc POST /admin/realms -d "{\"realm\":\"$REALM\",\"enabled\":true}")
  [[ "$http" == "201" || "$http" == "409" ]] || { echo "Realm create failed: $http"; exit 1; }
fi

echo "Creating/updating public client '$ADMIN_CLIENT_ID'..."
kc POST "/admin/realms/$REALM/clients" \
  -d "{\"clientId\":\"$ADMIN_CLIENT_ID\",\"publicClient\":true,\"redirectUris\":[\"http://localhost:8081/*\",\"http://127.0.0.1:8081/*\",\"http://localhost:18081/*\",\"http://127.0.0.1:18081/*\",\"http://localhost:8000/*\",\"http://127.0.0.1:8000/*\",\"http://admin-dashboard.local/*\"],\"webOrigins\":[\"*\",\"http://localhost:8081\",\"http://127.0.0.1:8081\",\"http://localhost:18081\",\"http://127.0.0.1:18081\",\"http://localhost:8000\",\"http://127.0.0.1:8000\",\"http://admin-dashboard.local\"],\"standardFlowEnabled\":true}" >/dev/null || true

echo "Creating/updating public client '$CUSTOMER_CLIENT_ID'..."
kc POST "/admin/realms/$REALM/clients" \
  -d "{\"clientId\":\"$CUSTOMER_CLIENT_ID\",\"publicClient\":true,\"redirectUris\":[\"http://localhost:8002/*\",\"http://127.0.0.1:8002/*\",\"http://customer-portal.local/*\"],\"webOrigins\":[\"*\",\"http://localhost:8002\",\"http://127.0.0.1:8002\",\"http://customer-portal.local\"],\"standardFlowEnabled\":true}" >/dev/null || true

echo "Creating/updating public client '$LANDING_CLIENT_ID'..."
{
  # Build redirectUris/webOrigins JSON arrays for landing client
  landing_redirects="\"http://localhost:8082/*\",\"http://127.0.0.1:8082/*\""
  landing_origins="\"*\",\"http://localhost:8082\",\"http://127.0.0.1:8082\""
  if [[ -n "$CODESPACES_URL" ]]; then
    landing_redirects+=",\"${CODESPACES_URL}/*\""
    landing_origins+=",\"${CODESPACES_URL}\""
  fi
  if [[ -n "$EXTRA_REDIRECT_JSON" ]]; then
    landing_redirects+=","$EXTRA_REDIRECT_JSON""
  fi
  if [[ -n "$EXTRA_ORIGINS_JSON" ]]; then
    landing_origins+=","$EXTRA_ORIGINS_JSON""
  fi
  kc POST "/admin/realms/$REALM/clients" \
    -d "{\"clientId\":\"$LANDING_CLIENT_ID\",\"publicClient\":true,\"redirectUris\":[${landing_redirects}],\"webOrigins\":[${landing_origins}],\"standardFlowEnabled\":true,\"implicitFlowEnabled\":true}" >/dev/null || true
}

ADMIN_CLIENT_UUID=$(get "/admin/realms/$REALM/clients?clientId=$ADMIN_CLIENT_ID" | jq -r '.[0].id')
CUSTOMER_CLIENT_UUID=$(get "/admin/realms/$REALM/clients?clientId=$CUSTOMER_CLIENT_ID" | jq -r '.[0].id')
LANDING_CLIENT_UUID=$(get "/admin/realms/$REALM/clients?clientId=$LANDING_CLIENT_ID" | jq -r '.[0].id')

# Ensure redirect URIs and web origins are updated if clients existed before
echo "Updating client redirectUris and webOrigins if necessary..."
kc PUT "/admin/realms/$REALM/clients/$ADMIN_CLIENT_UUID" -d "{\"redirectUris\":[\"http://localhost:8081/*\",\"http://127.0.0.1:8081/*\",\"http://localhost:18081/*\",\"http://127.0.0.1:18081/*\",\"http://localhost:8000/*\",\"http://127.0.0.1:8000/*\",\"http://admin-dashboard.local/*\"],\"webOrigins\":[\"*\",\"http://localhost:8081\",\"http://127.0.0.1:8081\",\"http://localhost:18081\",\"http://127.0.0.1:18081\",\"http://localhost:8000\",\"http://127.0.0.1:8000\",\"http://admin-dashboard.local\"]}" >/dev/null || true
kc PUT "/admin/realms/$REALM/clients/$CUSTOMER_CLIENT_UUID" -d "{\"redirectUris\":[\"http://localhost:8002/*\",\"http://127.0.0.1:8002/*\",\"http://customer-portal.local/*\"],\"webOrigins\":[\"*\",\"http://localhost:8002\",\"http://127.0.0.1:8002\",\"http://customer-portal.local\"]}" >/dev/null || true
{
  landing_redirects="\"http://localhost:8082/*\",\"http://127.0.0.1:8082/*\""
  landing_origins="\"*\",\"http://localhost:8082\",\"http://127.0.0.1:8082\""
  if [[ -n "$CODESPACES_URL" ]]; then
    landing_redirects+=",\"${CODESPACES_URL}/*\""
    landing_origins+=",\"${CODESPACES_URL}\""
  fi
  if [[ -n "$EXTRA_REDIRECT_JSON" ]]; then
    landing_redirects+=","$EXTRA_REDIRECT_JSON""
  fi
  if [[ -n "$EXTRA_ORIGINS_JSON" ]]; then
    landing_origins+=","$EXTRA_ORIGINS_JSON""
  fi
  kc PUT "/admin/realms/$REALM/clients/$LANDING_CLIENT_UUID" \
    -d "{\"redirectUris\":[${landing_redirects}],\"webOrigins\":[${landing_origins}],\"implicitFlowEnabled\":true,\"standardFlowEnabled\":true}" >/dev/null || true
}

# Create or update confidential client for APISIX gateway (authorization code flow)
echo "Creating/updating confidential client '$GATEWAY_CLIENT_ID' for APISIX..."
{
  # Callback used by APISIX
  gateway_redirects="\"http://nexus.local/callback\""
  # Allow optional extra redirects for non-prod (user-provided)
  if [[ -n "$EXTRA_REDIRECT_JSON" ]]; then
    gateway_redirects+=","$EXTRA_REDIRECT_JSON""
  fi
  kc POST "/admin/realms/$REALM/clients" \
    -d "{\"clientId\":\"$GATEWAY_CLIENT_ID\",\"publicClient\":false,\"protocol\":\"openid-connect\",\"redirectUris\":[${gateway_redirects}],\"standardFlowEnabled\":true,\"directAccessGrantsEnabled\":false,\"serviceAccountsEnabled\":false,\"attributes\":{\"pkce.code.challenge.method\":\"S256\"}}" >/dev/null || true
}

GATEWAY_CLIENT_UUID=$(get "/admin/realms/$REALM/clients?clientId=$GATEWAY_CLIENT_ID" | jq -r '.[0].id')

echo "Updating '$GATEWAY_CLIENT_ID' redirectUris if necessary..."
{
  gateway_redirects="\"http://nexus.local/callback\""
  if [[ -n "$EXTRA_REDIRECT_JSON" ]]; then
    gateway_redirects+=","$EXTRA_REDIRECT_JSON""
  fi
  kc PUT "/admin/realms/$REALM/clients/$GATEWAY_CLIENT_UUID" \
    -d "{\"redirectUris\":[${gateway_redirects}],\"standardFlowEnabled\":true,\"publicClient\":false}" >/dev/null || true
}

echo "Adding group mapper to gateway client..."
kc POST "/admin/realms/$REALM/clients/$GATEWAY_CLIENT_UUID/protocol-mappers/models" -d "$MAPPER_PAYLOAD" >/dev/null || true

echo "Fetching client secret for '$GATEWAY_CLIENT_ID'..."
GATEWAY_CLIENT_SECRET=$(get "/admin/realms/$REALM/clients/$GATEWAY_CLIENT_UUID/client-secret" | jq -r '.value')
if [[ -z "$GATEWAY_CLIENT_SECRET" || "$GATEWAY_CLIENT_SECRET" == "null" ]]; then
  echo "WARN: Could not fetch client secret for $GATEWAY_CLIENT_ID. Create one in Keycloak UI if missing." >&2
else
  echo "APISIX OIDC client: $GATEWAY_CLIENT_ID"
  echo "APISIX OIDC client secret: $GATEWAY_CLIENT_SECRET"
fi

echo "Ensuring groups..."
kc POST "/admin/realms/$REALM/groups" -d "{\"name\":\"$GROUP_ADMIN\"}" >/dev/null || true
kc POST "/admin/realms/$REALM/groups" -d "{\"name\":\"$GROUP_CUSTOMER\"}" >/dev/null || true

ADMIN_GROUP_ID=$(get "/admin/realms/$REALM/groups" | jq -r ".[] | select(.name==\"$GROUP_ADMIN\").id")
CUSTOMER_GROUP_ID=$(get "/admin/realms/$REALM/groups" | jq -r ".[] | select(.name==\"$GROUP_CUSTOMER\").id")

echo "Adding group membership claim mapper 'groups' to public clients..."
kc POST "/admin/realms/$REALM/clients/$ADMIN_CLIENT_UUID/protocol-mappers/models" -d "$MAPPER_PAYLOAD" >/dev/null || true
kc POST "/admin/realms/$REALM/clients/$CUSTOMER_CLIENT_UUID/protocol-mappers/models" -d "$MAPPER_PAYLOAD" >/dev/null || true
kc POST "/admin/realms/$REALM/clients/$LANDING_CLIENT_UUID/protocol-mappers/models" -d "$MAPPER_PAYLOAD" >/dev/null || true

echo "Creating users and assigning groups..."
kc POST "/admin/realms/$REALM/users" -d "{\"username\":\"$ADMIN_USER_ID\",\"email\":\"$ADMIN_USER_EMAIL\",\"enabled\":true}" >/dev/null || true
kc POST "/admin/realms/$REALM/users" -d "{\"username\":\"$CUSTOMER_USER_ID\",\"email\":\"$CUSTOMER_USER_EMAIL\",\"enabled\":true}" >/dev/null || true

ADMIN_ID=$(get "/admin/realms/$REALM/users?username=$ADMIN_USER_ID" | jq -r '.[0].id')
CUSTOMER_ID=$(get "/admin/realms/$REALM/users?username=$CUSTOMER_USER_ID" | jq -r '.[0].id')

kc PUT "/admin/realms/$REALM/users/$ADMIN_ID/reset-password" -d "{\"type\":\"password\",\"value\":\"$ADMIN_USER_PASS\",\"temporary\":false}" >/dev/null
kc PUT "/admin/realms/$REALM/users/$CUSTOMER_ID/reset-password" -d "{\"type\":\"password\",\"value\":\"$CUSTOMER_USER_PASS\",\"temporary\":false}" >/dev/null

kc PUT "/admin/realms/$REALM/users/$ADMIN_ID/groups/$ADMIN_GROUP_ID" >/dev/null || true
kc PUT "/admin/realms/$REALM/users/$CUSTOMER_ID/groups/$CUSTOMER_GROUP_ID" >/dev/null || true

echo "Done. Realm: $REALM, users: $ADMIN_USER_ID / $CUSTOMER_USER_ID"
echo "Clients: $ADMIN_CLIENT_ID ($ADMIN_CLIENT_UUID), $CUSTOMER_CLIENT_ID ($CUSTOMER_CLIENT_UUID), $LANDING_CLIENT_ID ($LANDING_CLIENT_UUID), $GATEWAY_CLIENT_ID ($GATEWAY_CLIENT_UUID)"
