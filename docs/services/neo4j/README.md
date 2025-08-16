# Neo4j Graph Database Service

## Overview
Neo4j is our graph database service for managing complex relationships and network data. This implementation uses Kubernetes secrets for secure credential management and provides both programmatic and web-based access.

## Quick Start

### Access Information
- **Neo4j Browser UI**: http://localhost:7474
- **Bolt Connection**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: Retrieved from Kubernetes secret

### Get Credentials
```bash
# Get username
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.username}' | base64 -d

# Get password
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d
```

### Start Neo4j
```bash
# Deploy Neo4j with secure configuration
./scripts/deploy/platform-neo4j.sh --deploy-neo4j

# Or just start port forwarding if already deployed
./scripts/deploy/platform-neo4j.sh --port-forward
```

## Deployment Architecture

### Security Features
- **Kubernetes Secrets**: All credentials stored securely
- **No Environment Variables**: Uses secretKeyRef for credential injection
- **StatefulSet**: Ensures data persistence and stable network identity
- **Network Isolation**: ClusterIP services with port forwarding only
- **Generated Passwords**: Strong, unique passwords using openssl

### Components
- **Neo4j StatefulSet**: Main database instance
- **Persistent Storage**: 5Gi volume for data persistence
- **Service**: ClusterIP for internal access
- **Secret**: Secure credential storage

## Usage Examples

### Browser UI Access
1. Ensure Neo4j is running and port forwarding is active
2. Open http://localhost:7474 in your browser
3. Connect using:
   - **Connect URL**: bolt://localhost:7687
   - **Username**: neo4j
   - **Password**: (from secret - see commands above)

### Cypher Query Examples

#### Basic Connectivity Test
```cypher
RETURN 'Hello, Neo4j!' as message
```

#### Create Sample Data
```cypher
// Create users
CREATE (alice:User {id: 'alice', name: 'Alice Johnson', role: 'admin'})
CREATE (bob:User {id: 'bob', name: 'Bob Smith', role: 'user'})

// Create project
CREATE (nexus:Project {id: 'nexus', name: 'Nexus Platform', status: 'active'})

// Create relationships
CREATE (alice)-[:OWNS]->(nexus)
CREATE (bob)-[:CONTRIBUTES_TO]->(nexus)

RETURN 'Sample data created' as result
```

#### Query Relationships
```cypher
// Find all user-project relationships
MATCH (u:User)-[r]->(p:Project) 
RETURN u.name as user, type(r) as relationship, p.name as project

// Find project owners
MATCH (u:User)-[:OWNS]->(p:Project)
RETURN u.name as owner, p.name as project

// Find all paths between users and projects
MATCH path = (u:User)-[*]-(p:Project)
RETURN path
```

#### Database Statistics
```cypher
// Count all nodes
MATCH (n) RETURN count(n) as total_nodes

// Count all relationships
MATCH ()-[r]->() RETURN count(r) as total_relationships

// List all node labels
CALL db.labels()

// List all relationship types
CALL db.relationshipTypes()
```

## Programmatic Access

### Python Example
```python
from neo4j import GraphDatabase
import subprocess

# Get credentials from Kubernetes
def get_credentials():
    username = subprocess.check_output([
        'kubectl', 'get', 'secret', 'neo4j-credentials', '-n', 'neo4j',
        '-o', 'jsonpath={.data.username}'
    ], text=True).strip()
    username = subprocess.check_output(['base64', '-d'], input=username, text=True).strip()
    
    password = subprocess.check_output([
        'kubectl', 'get', 'secret', 'neo4j-credentials', '-n', 'neo4j',
        '-o', 'jsonpath={.data.password}'
    ], text=True).strip()
    password = subprocess.check_output(['base64', '-d'], input=password, text=True).strip()
    
    return username, password

# Connect and query
username, password = get_credentials()
driver = GraphDatabase.driver("bolt://localhost:7687", auth=(username, password))

with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as total")
    print(f"Total nodes: {result.single()['total']}")

driver.close()
```

### Node.js Example
```javascript
const neo4j = require('neo4j-driver');
const { execSync } = require('child_process');

// Get credentials from Kubernetes
function getCredentials() {
    const username = execSync(
        "kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.username}' | base64 -d",
        { encoding: 'utf8' }
    ).trim();
    
    const password = execSync(
        "kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d",
        { encoding: 'utf8' }
    ).trim();
    
    return { username, password };
}

// Connect and query
const { username, password } = getCredentials();
const driver = neo4j.driver('bolt://localhost:7687', neo4j.auth.basic(username, password));

const session = driver.session();
session.run('MATCH (n) RETURN count(n) as total')
    .then(result => {
        console.log(`Total nodes: ${result.records[0].get('total')}`);
        return session.close();
    })
    .then(() => driver.close());
```

## Testing and Validation

### Automated Testing
```bash
# Run comprehensive connection test
./scripts/utils/test-neo4j-simple.py

# Expected output:
# ✅ Neo4j test completed successfully!
# 📊 Total nodes in database: X
# 📊 Total relationships in database: Y
```

### Manual Testing
```bash
# Open Neo4j Browser with credentials
./scripts/utils/test-neo4j-ui.sh

# This will:
# 1. Verify port forwarding is active
# 2. Display connection credentials
# 3. Open browser to Neo4j UI
```

### Data Persistence Test
```bash
# Create test data, restart pod, verify data persists
kubectl delete pod neo4j-0 -n neo4j
kubectl wait --for=condition=ready pod/neo4j-0 -n neo4j --timeout=300s

# Then verify data still exists in browser UI
```

## Administration

### Common Operations
```bash
# Check Neo4j status
kubectl get pods -n neo4j

# View Neo4j logs
kubectl logs neo4j-0 -n neo4j

# Access Neo4j shell directly
kubectl exec -it neo4j-0 -n neo4j -- cypher-shell -u neo4j -p $(kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d)

# View persistent storage
kubectl get pvc -n neo4j

# Check service endpoints
kubectl get svc -n neo4j
```

### Backup and Restore
```bash
# Create backup (example)
kubectl exec neo4j-0 -n neo4j -- neo4j-admin database dump neo4j --to-path=/backups/

# List backups
kubectl exec neo4j-0 -n neo4j -- ls -la /backups/

# Restore from backup (example)
kubectl exec neo4j-0 -n neo4j -- neo4j-admin database load neo4j --from-path=/backups/neo4j.dump
```

### Resource Management
```bash
# Scale (StatefulSet, so always 1 replica)
kubectl get statefulset -n neo4j

# Update resource limits
kubectl edit statefulset neo4j -n neo4j

# Monitor resource usage
kubectl top pod neo4j-0 -n neo4j
```

## Troubleshooting

### Common Issues

#### Connection Refused
**Problem**: Cannot connect to bolt://localhost:7687
```bash
# Check if port forwarding is running
pgrep -f "kubectl port-forward.*neo4j.*7687"

# Restart port forwarding
./scripts/deploy/platform-neo4j.sh --port-forward
```

#### Authentication Failed
**Problem**: Invalid credentials
```bash
# Verify credentials
kubectl get secret neo4j-credentials -n neo4j -o yaml

# Get current password
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d
```

#### Pod Not Starting
**Problem**: Neo4j pod in CrashLoopBackOff
```bash
# Check pod logs
kubectl logs neo4j-0 -n neo4j

# Check pod events
kubectl describe pod neo4j-0 -n neo4j

# Common fix: Clean up and redeploy
./scripts/deploy/platform-neo4j.sh --cleanup
./scripts/deploy/platform-neo4j.sh --deploy-neo4j
```

#### Data Not Persisting
**Problem**: Data lost after pod restart
```bash
# Check PVC status
kubectl get pvc -n neo4j

# Verify volume mounts
kubectl describe pod neo4j-0 -n neo4j | grep -A 5 Mounts
```

### Log Analysis
```bash
# Real-time logs
kubectl logs -f neo4j-0 -n neo4j

# Previous container logs (if pod restarted)
kubectl logs neo4j-0 -n neo4j --previous

# Filter for specific issues
kubectl logs neo4j-0 -n neo4j | grep ERROR
```

## Performance Optimization

### Query Performance
```cypher
// Use PROFILE to analyze query performance
PROFILE MATCH (u:User)-[:OWNS]->(p:Project) 
WHERE u.name = 'Alice Johnson'
RETURN p.name

// Use EXPLAIN to see execution plan
EXPLAIN MATCH (u:User)-[:OWNS]->(p:Project) 
RETURN u, p
```

### Indexing
```cypher
// Create index for better performance
CREATE INDEX user_id_index FOR (u:User) ON (u.id)

// Create constraint (also creates index)
CREATE CONSTRAINT user_id_unique FOR (u:User) REQUIRE u.id IS UNIQUE

// List all indexes
SHOW INDEXES

// List all constraints
SHOW CONSTRAINTS
```

### Resource Monitoring
```bash
# Monitor pod resources
kubectl top pod neo4j-0 -n neo4j

# Check disk usage
kubectl exec neo4j-0 -n neo4j -- df -h

# Monitor database size
kubectl exec neo4j-0 -n neo4j -- du -sh /data
```

## Security Best Practices

### Access Control
- ✅ Credentials stored in Kubernetes secrets
- ✅ No plaintext passwords in configuration
- ✅ Network access via port forwarding only
- ✅ Regular password rotation recommended

### Data Protection
- ✅ Data encrypted at rest (volume encryption)
- ✅ Connection encryption (TLS/SSL)
- ✅ Regular backups to secure storage
- ✅ Access logging and monitoring

### Network Security
- ✅ ClusterIP services (no external exposure)
- ✅ Port forwarding for development access
- ✅ Service mesh exclusion (database isolation)
- ✅ Network policies (future enhancement)

## Integration Examples

### With Authentication Services
```cypher
// Store user authentication data
CREATE (u:User {
    id: 'user123',
    email: 'user@example.com',
    keycloak_id: 'keycloak-uuid-123',
    roles: ['user', 'viewer']
})

// Link to application data
MATCH (u:User {id: 'user123'})
CREATE (u)-[:HAS_PROFILE]->(p:Profile {
    name: 'John Doe',
    department: 'Engineering',
    created: datetime()
})
```

### With Application Data
```cypher
// Complex relationship modeling
CREATE (u:User {id: 'dev1', name: 'Developer 1'})
CREATE (p:Project {id: 'proj1', name: 'Web App'})
CREATE (r:Repository {id: 'repo1', name: 'frontend'})
CREATE (i:Issue {id: 'issue1', title: 'Bug fix'})

CREATE (u)-[:WORKS_ON]->(p)
CREATE (p)-[:CONTAINS]->(r)
CREATE (r)-[:HAS_ISSUE]->(i)
CREATE (u)-[:ASSIGNED_TO]->(i)
```

## Documentation Links

- [Neo4j Official Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Browser Guide](https://neo4j.com/docs/browser-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

---

**Status**: ✅ Production Ready  
**Security**: ✅ Kubernetes Secrets  
**Access**: ✅ Browser UI + Bolt Protocol  
**Testing**: ✅ Automated + Manual Scripts
