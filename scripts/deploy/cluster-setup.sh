#!/bin/bash

# ==============================================================================
# Cluster Setup Script
#
# Description:
#   This script automates the setup of a Kubernetes cluster for the Nexus
#   platform. It is designed to be non-destructive and provides pre-flight
#   checks to ensure all dependencies are met. It supports multiple cluster
#   providers, with specific logic for local development (Kind) and guidance
#   for cloud environments managed by Terraform.
#
# Usage:
#   For local 'kind' cluster:
#     ./scripts/deploy/cluster-setup.sh --provider kind --config /path/to/dev.env
#
#   For cloud providers (Terraform-managed):
#     ./scripts/deploy/cluster-setup.sh --provider digitalocean
#
# Parameters:
#   --provider <name>   : Required. The cluster provider to use.
#                         Supported: 'kind', 'digitalocean', 'gke', 'eks', 'aks'.
#   --config <path>     : Required for 'kind' provider. Path to the environment
#                         file containing cluster configuration.
#
# ==============================================================================

set -eo pipefail

# --- Helper Functions for Colored Output ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}


# --- Usage Function ---
usage() {
    echo "Usage: $0 --provider <provider> [--config /path/to/env.file]"
    echo ""
    echo "This script sets up the Kubernetes cluster for the Nexus platform."
    echo ""
    echo "Options:"
    echo "  --provider <name>   Required. The cluster provider to use."
    echo "                      Supported: 'kind', 'digitalocean', 'gke', 'eks', 'aks'."
    echo "  --config <path>     Path to the environment file. Required only for the 'kind' provider."
    echo "  --help              Display this help message."
    echo ""
    exit 1
}

# --- Argument Parsing ---
CLUSTER_PROVIDER=""
ENV_FILE=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --provider) CLUSTER_PROVIDER="$2"; shift ;;
        --config) ENV_FILE="$2"; shift ;;
        --help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# --- Pre-flight Checks ---
check_dependencies() {
    info "Performing pre-flight checks for required tools..."
    local missing_deps=0
    local deps=("kubectl" "helm")

    # Kind is only required if the provider is 'kind'
    if [[ "$CLUSTER_PROVIDER" == "kind" ]]; then
        deps+=("kind" "docker")
    fi
    
    # Terraform is needed for cloud providers
    if [[ "$CLUSTER_PROVIDER" != "kind" ]]; then
        deps+=("terraform")
    fi

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            warn "Dependency '$dep' is not installed. Please install it and try again."
            missing_deps=1
        else
            info "   ✅ '$dep' is installed."
        fi
    done

    if [ "$missing_deps" -eq 1 ]; then
        error "Aborting due to missing dependencies."
    fi
    success "All dependencies are satisfied."
    echo ""
}


# Validate arguments
if [ -z "$CLUSTER_PROVIDER" ]; then
    error "--provider is a required argument."
    usage
fi

if [[ "$CLUSTER_PROVIDER" == "kind" ]] && [ -z "$ENV_FILE" ]; then
    error "--config is required when using the 'kind' provider."
    usage
fi

# Now that provider is known, run dependency checks
check_dependencies


# --- Source Environment File (if provided for kind) ---
if [ -n "$ENV_FILE" ]; then
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file not found at: $ENV_FILE"
    fi
    info "Sourcing environment variables from $ENV_FILE..."
    set -a # Automatically export all variables
    source "$ENV_FILE"
    set +a
    info " done."
    echo ""
fi


# --- Kind Cluster Setup ---
setup_kind_cluster() {
    if [ -z "$KIND_CLUSTER_NAME" ]; then
        error "KIND_CLUSTER_NAME is not defined in the environment file."
    fi

    info "Starting setup for 'kind' cluster: '$KIND_CLUSTER_NAME'..."

    if kind get clusters | grep -q "^$KIND_CLUSTER_NAME$"; then
        warn "Cluster '$KIND_CLUSTER_NAME' already exists. No action needed."
    else
        info "Cluster '$KIND_CLUSTER_NAME' not found. Creating..."
        if [ -z "$KIND_CONFIG_PATH" ] || [ ! -f "$KIND_CONFIG_PATH" ]; then
            warn "KIND_CONFIG_PATH not specified or invalid. Using default kind configuration."
            kind create cluster --name "$KIND_CLUSTER_NAME"
        else
            info "Using Kind configuration from: $KIND_CONFIG_PATH"
            kind create cluster --name "$KIND_CLUSTER_NAME" --config "$KIND_CONFIG_PATH"
        fi
        success "Successfully created cluster '$KIND_CLUSTER_NAME'."
    fi

    info "Creating core platform namespaces..."
    kubectl create namespace nexus-platform || true
    kubectl create namespace nexus-services || true
    
    info "Verifying cluster context..."
    kubectl cluster-info --context "kind-$KIND_CLUSTER_NAME"
    success "Cluster setup complete."
}

# --- Main Execution ---
echo "================================================="
echo "        Nexus Platform Cluster Setup"
echo "================================================="
info "Provider: $CLUSTER_PROVIDER"
echo ""

case "$CLUSTER_PROVIDER" in
    "kind")
        setup_kind_cluster
        ;;
    "digitalocean"|"gke"|"eks"|"aks")
        info "Provider '$CLUSTER_PROVIDER' selected. This process is managed by Terraform."
        warn "This script will not create the cluster. Please use the Terraform scripts."
        info "Example for DigitalOcean:"
        info "  cd iac/terraform/environments/digitalocean/dev"
        info "  terraform init"
        info "  terraform apply"
        exit 0
        ;;
    *)
        error "Unsupported CLUSTER_PROVIDER: '$CLUSTER_PROVIDER'."
        usage
        ;;
esac

exit 0
