#!/usr/bin/env python3
"""
Simple Neo4j Connection Test Script
===================================
This script tests basic connectivity to Neo4j and performs simple operations.
"""

import os
import sys
import subprocess
from neo4j import GraphDatabase

def get_credentials():
    """Get Neo4j credentials from Kubernetes secret"""
    try:
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
    except subprocess.CalledProcessError as e:
        print(f"Failed to get credentials: {e}")
        return None, None

def test_connection():
    """Test Neo4j connection and perform basic operations"""
    print("Neo4j Connection Test")
    print("====================")
    
    # Get credentials
    username, password = get_credentials()
    if not username or not password:
        print("❌ Failed to retrieve credentials")
        return False
    
    print(f"✓ Retrieved credentials for user: {username}")
    
    # Connection details
    uri = "bolt://localhost:7687"
    
    try:
        # Connect to Neo4j
        print(f"📡 Connecting to {uri}...")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Use default database for Community Edition
        with driver.session() as session:
            # Test basic connectivity
            result = session.run("RETURN 'Hello, Neo4j!' as message")
            record = result.single()
            print(f"✓ Connection successful: {record['message']}")
            
            # Create some test data
            print("\n📝 Creating test data...")
            session.run("""
                MERGE (u:User {id: 'test-user-1', name: 'Alice Johnson', role: 'admin'})
                MERGE (u2:User {id: 'test-user-2', name: 'Bob Smith', role: 'user'})
                MERGE (p:Project {id: 'test-project-1', name: 'Nexus Platform', status: 'active'})
                MERGE (u)-[:OWNS]->(p)
                MERGE (u2)-[:CONTRIBUTES_TO]->(p)
            """)
            print("✓ Test data created")
            
            # Query test data
            print("\n🔍 Querying test data...")
            result = session.run("""
                MATCH (u:User)-[r]->(p:Project)
                RETURN u.name as user, type(r) as relationship, p.name as project
                ORDER BY u.name
            """)
            
            for record in result:
                print(f"  👤 {record['user']} {record['relationship']} {record['project']}")
            
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()['total_nodes']
            print(f"\n📊 Total nodes in database: {total_nodes}")
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
            total_relationships = result.single()['total_relationships']
            print(f"📊 Total relationships in database: {total_relationships}")
            
        driver.close()
        print("\n✅ Neo4j test completed successfully!")
        print(f"🌐 Browser UI available at: http://localhost:7474")
        print(f"🔌 Bolt connection available at: {uri}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
