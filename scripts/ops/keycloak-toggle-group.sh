#!/usr/bin/env bash
set -euo pipefail

# Toggle a user's membership in a Keycloak group (add/remove)
# Usage:
#   KEYCLOAK_URL=http://localhost:8080 KEYCLOAK_ADMIN=admin KEYCLOAK_ADMIN_PASSWORD=admin \
#   ./scripts/ops/keycloak-toggle-group.sh nexus alice-admin platform-admins add
#   ./scripts/ops/keycloak-toggle-group.sh nexus bob-customer customers remove

KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:8080}
ADMIN_USER=${KEYCLOAK_ADMIN:-admin}
ADMIN_PASS=${KEYCLOAK_ADMIN_PASSWORD:-admin}

REALM="${1:-nexus}"
USERNAME="${2:?username required}"
GROUP_NAME="${3:?group required}"
ACTION="${4:-add}" # add|remove

ACCESS_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d 'grant_type=password' \
  -d 'client_id=admin-cli' | jq -r .access_token)

kc_get() { curl -s -X GET "$KEYCLOAK_URL$1" -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json'; }
kc() { local m="$1"; shift; local p="$1"; shift; curl -s -o /dev/null -w "%{http_code}" -X "$m" "$KEYCLOAK_URL$p" -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' "$@"; }

USER_ID=$(kc_get "/admin/realms/$REALM/users?username=$USERNAME" | jq -r '.[0].id')
GROUP_ID=$(kc_get "/admin/realms/$REALM/groups" | jq -r ".[] | select(.name==\"$GROUP_NAME\").id")

if [[ -z "$USER_ID" || "$USER_ID" == "null" ]]; then echo "User not found"; exit 1; fi
if [[ -z "$GROUP_ID" || "$GROUP_ID" == "null" ]]; then echo "Group not found"; exit 1; fi

if [[ "$ACTION" == "add" ]]; then
  code=$(kc PUT "/admin/realms/$REALM/users/$USER_ID/groups/$GROUP_ID")
  echo "Add group result: $code"
else
  code=$(kc DELETE "/admin/realms/$REALM/users/$USER_ID/groups/$GROUP_ID")
  echo "Remove group result: $code"
fi
