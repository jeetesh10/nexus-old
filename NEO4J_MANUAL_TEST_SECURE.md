# Neo4j Manual Test - Secure Implementation

## Overview
This document provides step-by-step instructions for testing the Neo4j deployment in our secure, production-ready environment.

## Prerequisites
- Kubernetes cluster running (kind)
- Neo4j deployed via `./scripts/deploy/platform-neo4j.sh`
- Port forwarding active for Neo4j services

## Deployment Status
✅ **Secure Implementation Complete**
- Using Kubernetes secrets for credential management
- No environment variables for sensitive data
- StatefulSet deployment for data persistence
- Official Neo4j Docker image
- Community Edition (single database)

## Connection Details

### Browser UI Access
- **URL**: http://localhost:7474
- **Username**: neo4j
- **Password**: Retrieved from Kubernetes secret

### Bolt Connection
- **URI**: bolt://localhost:7687
- **Database**: Default (Community Edition)

## Test Procedures

### 1. Quick Script Test
```bash
# Run automated connection test
./scripts/utils/test-neo4j-simple.py

# Expected output:
# ✅ Neo4j test completed successfully!
# 📊 Total nodes in database: 3
# 📊 Total relationships in database: 2
```

### 2. Browser UI Test
```bash
# Open Neo4j Browser with credentials
./scripts/utils/test-neo4j-ui.sh

# Manually verify:
# 1. Browser opens to http://localhost:7474
# 2. Connect with provided credentials
# 3. Dashboard loads successfully
```

### 3. Manual Cypher Queries

#### Basic Connectivity Test
```cypher
RETURN 'Hello, Neo4j!' as message
```

#### View Test Data
```cypher
MATCH (n) RETURN n LIMIT 25
```

#### Relationship Queries
```cypher
MATCH (u:User)-[r]->(p:Project) 
RETURN u.name as user, type(r) as relationship, p.name as project
```

#### Database Statistics
```cypher
// Count all nodes
MATCH (n) RETURN count(n) as total_nodes

// Count all relationships
MATCH ()-[r]->() RETURN count(r) as total_relationships

// List node labels
CALL db.labels()

// List relationship types
CALL db.relationshipTypes()
```

## Security Verification

### 1. Credential Security
```bash
# Verify credentials are in Kubernetes secrets (not env vars)
kubectl get secret neo4j-credentials -n neo4j -o yaml

# Should show base64 encoded values, not plaintext
```

### 2. Network Security
```bash
# Verify Neo4j is only accessible via port forwarding
kubectl get svc -n neo4j

# Should show ClusterIP (internal only), not LoadBalancer/NodePort
```

### 3. Pod Security
```bash
# Check pod security context
kubectl get pod neo4j-0 -n neo4j -o yaml | grep -A 10 securityContext

# Verify StatefulSet for persistence
kubectl get statefulset -n neo4j
```

## Data Persistence Test

### 1. Create Sample Data
```cypher
// Create users
CREATE (alice:User {id: 'alice', name: 'Alice Johnson', role: 'admin'})
CREATE (bob:User {id: 'bob', name: 'Bob Smith', role: 'user'})
CREATE (carol:User {id: 'carol', name: 'Carol Davis', role: 'developer'})

// Create projects
CREATE (nexus:Project {id: 'nexus', name: 'Nexus Platform', status: 'active'})
CREATE (api:Project {id: 'api', name: 'API Gateway', status: 'development'})

// Create relationships
CREATE (alice)-[:OWNS]->(nexus)
CREATE (bob)-[:CONTRIBUTES_TO]->(nexus)
CREATE (carol)-[:DEVELOPS]->(api)
CREATE (alice)-[:MANAGES]->(api)

RETURN 'Sample data created' as result
```

### 2. Verify Data Persistence
```bash
# Restart Neo4j pod
kubectl delete pod neo4j-0 -n neo4j

# Wait for pod to restart
kubectl wait --for=condition=ready pod/neo4j-0 -n neo4j --timeout=300s

# Verify data still exists (run in Browser)
MATCH (n) RETURN count(n) as total_nodes
```

## Performance Test

### 1. Basic Performance Query
```cypher
// Create performance test data
UNWIND range(1, 1000) as i
CREATE (u:TestUser {id: i, name: 'User' + toString(i)})
CREATE (p:TestProject {id: i, name: 'Project' + toString(i)})
CREATE (u)-[:WORKS_ON]->(p)
```

### 2. Query Performance
```cypher
// Time this query
PROFILE MATCH (u:TestUser)-[:WORKS_ON]->(p:TestProject)
WHERE u.id > 500
RETURN count(*)
```

## Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if port forwarding is running
pgrep -f "kubectl port-forward.*neo4j"

# Restart port forwarding if needed
./scripts/deploy/platform-neo4j.sh --port-forward
```

#### Pod Not Starting
```bash
# Check pod logs
kubectl logs neo4j-0 -n neo4j

# Check pod events
kubectl describe pod neo4j-0 -n neo4j
```

#### Authentication Issues
```bash
# Verify credentials
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.username}' | base64 -d
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d
```

## Success Criteria

### ✅ Deployment Success
- [ ] Neo4j pod running and ready
- [ ] Services created and accessible
- [ ] Persistent volumes mounted
- [ ] Secrets properly configured

### ✅ Connectivity Success
- [ ] Browser UI accessible at http://localhost:7474
- [ ] Bolt connection working at bolt://localhost:7687
- [ ] Authentication successful
- [ ] Basic queries execute successfully

### ✅ Security Success
- [ ] No hardcoded credentials in deployment files
- [ ] Credentials stored in Kubernetes secrets
- [ ] Services use ClusterIP (internal only)
- [ ] No environment variables for sensitive data

### ✅ Persistence Success
- [ ] Data survives pod restarts
- [ ] StatefulSet maintains identity
- [ ] Volumes properly mounted and writable

## Next Steps

After successful testing:
1. **Commit Changes**: Commit the Neo4j deployment to version control
2. **Documentation**: Update platform documentation with Neo4j integration
3. **PostgreSQL**: Proceed with PostgreSQL deployment using the same security patterns
4. **Integration**: Plan integration between services (Keycloak, MongoDB, Neo4j)

## Support Commands

```bash
# Get all Neo4j resources
kubectl get all -n neo4j

# Get credentials quickly
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.username}' | base64 -d && echo
kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d && echo

# Access Neo4j directly (if needed)
kubectl exec -it neo4j-0 -n neo4j -- cypher-shell -u neo4j -p $(kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d)
```

---

**Status**: ✅ Ready for Production  
**Security**: ✅ Kubernetes Secrets  
**Persistence**: ✅ StatefulSet + PVC  
**Testing**: ✅ Automated + Manual
