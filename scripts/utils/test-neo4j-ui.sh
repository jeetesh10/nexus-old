#!/bin/bash
set -euo pipefail

echo "Neo4j Browser UI Test"
echo "===================="

# Check if port forwarding is active
if ! pgrep -f "kubectl port-forward.*neo4j.*7474" > /dev/null; then
    echo "❌ Neo4j port forwarding not active"
    echo "Run: ./scripts/deploy/platform-neo4j.sh --port-forward"
    exit 1
fi

echo "✓ Neo4j port forwarding is active"

# Get credentials
echo "🔑 Retrieving Neo4j credentials..."
USERNAME=$(kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.username}' | base64 -d)
PASSWORD=$(kubectl get secret neo4j-credentials -n neo4j -o jsonpath='{.data.password}' | base64 -d)

echo "✓ Credentials retrieved"
echo ""
echo "Neo4j Browser Access"
echo "==================="
echo "🌐 URL: http://localhost:7474"
echo "👤 Username: $USERNAME"
echo "🔑 Password: $PASSWORD"
echo ""
echo "Connection String for Bolt:"
echo "bolt://localhost:7687"
echo ""
echo "📝 Manual Test Steps:"
echo "1. Open http://localhost:7474 in your browser"
echo "2. Connect using the credentials above"
echo "3. Run this query to see test data:"
echo "   MATCH (n) RETURN n LIMIT 25"
echo ""
echo "4. Try this query to see relationships:"
echo "   MATCH (u:User)-[r]->(p:Project) RETURN u, r, p"
echo ""

# Try to open the browser (macOS)
if command -v open > /dev/null; then
    echo "🚀 Opening Neo4j Browser..."
    open "http://localhost:7474"
else
    echo "ℹ️ Please manually open http://localhost:7474 in your browser"
fi
