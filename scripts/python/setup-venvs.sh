#!/usr/bin/env bash
set -euo pipefail

# Create per-service Python virtual environments and install requirements.
# Usage:
#   scripts/python/setup-venvs.sh            # create venvs where missing and install requirements
#   scripts/python/setup-venvs.sh --recreate # recreate venvs (delete and re-create) for all services
#   scripts/python/setup-venvs.sh --service services/admin-dashboard-service  # only this service
#
# Each venv is created inside the service directory and named <folder>-venv, e.g. services/foo/foo-venv

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
RECREATE="false"
SERVICE_FILTER=""

while [[ ${1:-} =~ ^- ]]; do
  case "${1:-}" in
    --recreate) RECREATE="true"; shift ;;
    --service) SERVICE_FILTER="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '1,40p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

mapfile -t REQS < <(find services -type f -name requirements.txt | sort)

if [[ -n "$SERVICE_FILTER" ]]; then
  REQS=("$SERVICE_FILTER/requirements.txt")
fi

if [[ ${#REQS[@]} -eq 0 ]]; then
  echo "No Python services with requirements.txt found under services/" >&2
  exit 0
fi

created=0
updated=0

for req in "${REQS[@]}"; do
  svc_dir="$(dirname "$req")"
  svc_name="$(basename "$svc_dir")"
  venv_path="$svc_dir/${svc_name}-venv"

  if [[ "$RECREATE" == "true" && -d "$venv_path" ]]; then
    echo "[recreate] Removing existing venv: $venv_path"
    rm -rf "$venv_path"
  fi

  if [[ ! -d "$venv_path" ]]; then
    echo "[create] $svc_name -> $venv_path"
    python3 -m venv "$venv_path"
    created=$((created+1))
  else
    echo "[reuse]  $svc_name -> $venv_path"
    updated=$((updated+1))
  fi

  # shellcheck disable=SC1090
  source "$venv_path/bin/activate"
  python -m pip install --upgrade pip setuptools wheel >/dev/null
  echo "[pip]    Installing: $req"
  pip install -r "$req"
  deactivate || true

  echo "[done]   $svc_name"
  echo
done

echo "Summary: created=$created reused=$updated"
echo "Tip: to activate a service venv -> source <service>/<service>-venv/bin/activate"
