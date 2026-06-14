#!/usr/bin/env bash
# Kind Cluster Management Script for IICPC Platform
# Usage: ./scripts/kind-cluster.sh [create|delete|load-images|status|logs]

set -euo pipefail

CLUSTER_NAME="iicpc"
KIND_CONFIG="kind-config.yaml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_dependencies() {
    local missing=()
    for cmd in kind docker kubectl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install: kind (https://kind.sigs.k8s.io), docker, kubectl"
        exit 1
    fi
}

create_cluster() {
    log_info "Creating Kind cluster '$CLUSTER_NAME'..."
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_warn "Cluster '$CLUSTER_NAME' already exists"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
    
    log_info "Waiting for nodes to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s
    
    log_success "Cluster '$CLUSTER_NAME' created successfully"
    
    # Show cluster info
    log_info "Cluster nodes:"
    kubectl get nodes -o wide
}

delete_cluster() {
    log_info "Deleting Kind cluster '$CLUSTER_NAME'..."
    kind delete cluster --name "$CLUSTER_NAME"
    log_success "Cluster '$CLUSTER_NAME' deleted"
}

load_images() {
    log_info "Loading Docker images into Kind cluster..."
    
    local images=(
        "iicpc-hosting:latest"
        "iicpc-botfleet:latest"
        "iicpc-evaluation:latest"
        "iicpc-federation:latest"
        "iicpc-governance:latest"
        "iicpc-strategic:latest"
        "iicpc-dashboard:latest"
    )
    
    for img in "${images[@]}"; do
        log_info "Loading $img..."
        kind load docker-image "$img" --name "$CLUSTER_NAME" || log_warn "Failed to load $img (image may not exist locally)"
    done
    
    log_success "Images loaded"
}

show_status() {
    log_info "Cluster: $CLUSTER_NAME"
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_success "Cluster exists"
        echo ""
        log_info "Nodes:"
        kubectl get nodes -o wide
        echo ""
        log_info "Pods (all namespaces):"
        kubectl get pods -A -o wide
        echo ""
        log_info "Services:"
        kubectl get svc -A
    else
        log_warn "Cluster does not exist"
    fi
}

show_logs() {
    log_info "Showing control plane logs..."
    kind export logs --name "$CLUSTER_NAME" /tmp/kind-logs 2>/dev/null || true
    ls -la /tmp/kind-logs/
}

case "${1:-}" in
    create)
        check_dependencies
        create_cluster
        ;;
    delete)
        check_dependencies
        delete_cluster
        ;;
    load-images)
        check_dependencies
        load_images
        ;;
    status)
        check_dependencies
        show_status
        ;;
    logs)
        check_dependencies
        show_logs
        ;;
    *)
        echo "Usage: $0 {create|delete|load-images|status|logs}"
        echo ""
        echo "Commands:"
        echo "  create       - Create the Kind cluster"
        echo "  delete       - Delete the Kind cluster"
        echo "  load-images  - Load local Docker images into cluster"
        echo "  status       - Show cluster status (nodes, pods, services)"
        echo "  logs         - Export cluster logs"
        exit 1
        ;;
esac