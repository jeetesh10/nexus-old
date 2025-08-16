# Platform Orchestrator

## Overview
The Nexus Platform Orchestrator is a simple, unified script that manages the entire platform ecosystem by calling our modular deployment scripts in the correct sequence.

## Design Philosophy
- **Simple**: Calls existing modular scripts, doesn't reinvent them
- **Sequential**: Deploys services in proper dependency order
- **Secure**: All security handled by the individual deployment scripts
- **Observable**: Clear status reporting and testing capabilities

## Quick Start

### Check Current Status
```bash
./scripts/platform/orchestrator.sh status
```

### Deploy Everything
```bash
./scripts/platform/orchestrator.sh deploy-all
```

### Deploy Only Databases
```bash
./scripts/platform/orchestrator.sh deploy-databases
```

## Commands

### Deployment Commands
- **`deploy-all`** - Deploy complete platform (core + databases)
- **`deploy-core`** - Deploy core platform only (Keycloak + infrastructure)
- **`deploy-databases`** - Deploy all databases (MongoDB + Neo4j)

### Management Commands
- **`status`** - Show status of all services with color coding
- **`test-all`** - Run automated tests for all services
- **`cleanup-databases`** - Clean up only database services
- **`cleanup-all`** - Clean up entire platform (with confirmation)

### Information Commands
- **`help`** - Show usage information

## Deployment Sequence

The orchestrator follows this precise sequence:

### Core Platform (`deploy-core`)
1. **Infrastructure Setup** (`verify-setup.sh`)
   - Vault (secret management)
   - External Secrets Operator
   - Linkerd (service mesh)
2. **Keycloak** (`platform-keycloak.sh --deploy-keycloak`)
   - Identity and access management

### Database Layer (`deploy-databases`)
3. **MongoDB** (`platform-mongodb.sh --deploy-mongodb`)
   - Document database + Mongo Express UI
4. **Neo4j** (`platform-neo4j.sh --deploy-neo4j`)
   - Graph database + Browser UI

### Future Components
5. **PostgreSQL** (planned)
   - Relational database for Keycloak backend

## Status Reporting

The status command provides comprehensive visibility:

```bash
$ ./scripts/platform/orchestrator.sh status

================================
Platform Status
================================
Core Infrastructure:
-------------------
✅ Vault: RUNNING
❌ External Secrets: STOPPED
❌ Linkerd: STOPPED

Application Services:
--------------------
✅ Keycloak: RUNNING (http://localhost:8080)

Database Services:
-----------------
✅ MongoDB: RUNNING (mongodb://localhost:27017)
✅ Mongo Express: RUNNING (http://localhost:8081)
✅ Neo4j: RUNNING (http://localhost:7474, bolt://localhost:7687)

Port Forwarding Status:
----------------------
✅ Keycloak port forward: ACTIVE
✅ MongoDB port forward: ACTIVE
✅ Mongo Express port forward: ACTIVE
✅ Neo4j port forward: ACTIVE
```

### Status Color Coding
- 🟢 **GREEN** - Service running and healthy
- 🔴 **RED** - Service stopped or failed
- 🟡 **YELLOW** - Service starting or warning state

## Testing Integration

### Automated Testing
```bash
./scripts/platform/orchestrator.sh test-all
```

This runs:
- MongoDB connection and data tests
- Neo4j connection and graph tests
- Future: Keycloak and PostgreSQL tests

### Prerequisites for Testing
```bash
# Install Python dependencies for tests
pip install pymongo neo4j
```

## Script Architecture

The orchestrator is intentionally simple:

```bash
# Core Functions
deploy_core()           # Calls verify-setup.sh + platform-keycloak.sh
deploy_databases()      # Calls platform-mongodb.sh + platform-neo4j.sh
show_status()           # Checks pod status via kubectl
test_all()              # Calls test scripts for each service
cleanup_*()             # Calls cleanup functions in reverse order
```

### Security Model
- **No credentials handled** - All security managed by individual scripts
- **No configuration files** - Uses existing modular scripts as-is
- **Read-only operations** - Status and testing don't modify anything

## Troubleshooting

### Common Issues

#### Services Show as STOPPED But Are Running
```bash
# Check actual pod status
kubectl get pods --all-namespaces

# The orchestrator status might need refresh
./scripts/platform/orchestrator.sh status
```

#### Tests Fail Due to Missing Dependencies
```bash
# Install Python packages
pip install pymongo neo4j

# Or use the individual test scripts directly
python3 scripts/utils/test-mongodb-simple.py
python3 scripts/utils/test-neo4j-simple.py
```

#### Port Forwarding Issues
```bash
# The individual scripts handle port forwarding
# If needed, restart port forwarding manually:
./scripts/deploy/platform-mongodb.sh --port-forward
./scripts/deploy/platform-neo4j.sh --port-forward
```

## Customization

### Adding New Services
To add a new service to the orchestrator:

1. **Create the deployment script** following the pattern:
   ```bash
   scripts/deploy/platform-newservice.sh --deploy-newservice
   scripts/deploy/platform-newservice.sh --cleanup
   ```

2. **Add to orchestrator** in the appropriate deployment function:
   ```bash
   deploy_databases() {
       # ... existing services ...
       log_info "Step 3: Deploying New Service..."
       bash "$DEPLOY_DIR/platform-newservice.sh" --deploy-newservice
   }
   ```

3. **Add status check** in `show_status()`:
   ```bash
   # Check New Service
   if kubectl get pod newservice-0 -n newservice 2>/dev/null | grep -q "Running"; then
       echo -e "✅ New Service: ${GREEN}RUNNING${NC}"
   else
       echo -e "❌ New Service: ${RED}STOPPED${NC}"
   fi
   ```

### Environment Support
The orchestrator currently operates in development mode. For QA/Production:

```bash
# Future enhancement - environment-specific configs
export ENVIRONMENT=qa
./scripts/platform/orchestrator.sh deploy-all
```

## Integration with CI/CD

### GitLab CI Example
```yaml
deploy_platform:
  script:
    - ./scripts/platform/orchestrator.sh deploy-all
    - ./scripts/platform/orchestrator.sh test-all
  only:
    - main
```

### GitHub Actions Example
```yaml
- name: Deploy Platform
  run: ./scripts/platform/orchestrator.sh deploy-all
  
- name: Test Platform
  run: ./scripts/platform/orchestrator.sh test-all
```

## Monitoring Integration

### Health Checks for External Monitoring
```bash
# Use status command for monitoring systems
if ./scripts/platform/orchestrator.sh status | grep -q "❌"; then
    echo "Platform has unhealthy services"
    exit 1
fi
```

### Prometheus Integration
The individual deployment scripts include monitoring endpoints that can be scraped by Prometheus.

## Best Practices

### Daily Operations
```bash
# Morning: Check platform status
./scripts/platform/orchestrator.sh status

# If issues found: Test specific services
./scripts/platform/orchestrator.sh test-all

# Emergency: Quick redeploy
./scripts/platform/orchestrator.sh cleanup-databases
./scripts/platform/orchestrator.sh deploy-databases
```

### Maintenance Windows
```bash
# Planned maintenance
./scripts/platform/orchestrator.sh cleanup-all
# Perform maintenance
./scripts/platform/orchestrator.sh deploy-all
./scripts/platform/orchestrator.sh test-all
```

---

## File Structure

```
scripts/platform/
├── orchestrator.sh              # Main orchestrator script
└── ...

scripts/deploy/
├── platform-keycloak.sh         # Keycloak deployment
├── platform-mongodb.sh          # MongoDB deployment
├── platform-neo4j.sh            # Neo4j deployment
└── platform-postgresql.sh       # PostgreSQL (future)

scripts/utils/
├── verify-setup.sh              # Core infrastructure setup
├── test-mongodb-simple.py       # MongoDB testing
├── test-neo4j-simple.py         # Neo4j testing
└── ...
```

**Philosophy**: Simple orchestration that leverages existing modular scripts for maximum maintainability and minimal complexity.
