#!/usr/bin/env bash
set -euo pipefail

# Adds current origin as redirect URI for admin-dashboard client in the 'nexus' realm
# Usage: CODESPACES_URL="https://<id>-8082.app.github.dev" KEYCLOAK_URL="http://127.0.0.1:11000" ./scripts/ops/add-redirect-uri.sh

KEYCLOAK_URL=${KEYCLOAK_URL:-http://127.0.0.1:11000}
REALM=${KEYCLOAK_REALM:-nexus}
CLIENT_ID=${CLIENT_ID:-admin-dashboard}

if [[ -z "${CODESPACES_URL:-}" ]]; then
  echo "Set CODESPACES_URL to your landing page origin (e.g., https://<id>-8082.app.github.dev)" >&2
  exit 1
fi

echo "Fetching admin token..."
ACCESS_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=${KEYCLOAK_ADMIN:-admin}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD:-admin}" \
  -d 'grant_type=password' \
  -d 'client_id=admin-cli' | jq -r .access_token)

[[ -n "$ACCESS_TOKEN" && "$ACCESS_TOKEN" != null ]] || { echo "Failed to get token"; exit 1; }

echo "Getting client UUID..."
CLIENT_UUID=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "$KEYCLOAK_URL/admin/realms/$REALM/clients?clientId=$CLIENT_ID" | jq -r '.[0].id')
[[ -n "$CLIENT_UUID" && "$CLIENT_UUID" != null ]] || { echo "Client not found: $CLIENT_ID"; exit 1; }

echo "Fetching client..."
CLIENT_JSON=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID")

ORIGIN_NO_STAR=$(echo "$CODESPACES_URL" | sed 's#/\*$##')
LANDING_HTML="${ORIGIN_NO_STAR%/}/landing-page.html"
NEW_CLIENT=$(echo "$CLIENT_JSON" | jq \
  --arg uri_wild "$CODESPACES_URL/*" \
  --arg uri_exact "$LANDING_HTML" \
  --arg origin "$ORIGIN_NO_STAR" \
  '.["redirectUris"] as $r | . as $root |\
   (if ($r|index($uri_wild)) then . else .redirectUris += [$uri_wild] end)\
   | (.["redirectUris"] as $r2 | if ($r2|index($uri_exact)) then . else .redirectUris += [$uri_exact] end)\
   | (.["webOrigins"] //= [])\
   | (if ((.["webOrigins"]|index($origin))) then . else .webOrigins += [$origin] end)')

echo "Updating client redirectUris..."
curl -s -o /dev/null -w "%{http_code}\n" -X PUT \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$NEW_CLIENT" \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID"

echo "Done"
