#!/usr/bin/env python3
"""
MongoDB Test Script
==================

This script tests MongoDB connectivity and creates test collections/documents
that you can verify through MongoDB UI tools like MongoDB Compass.

Requirements:
- pymongo (pip install pymongo)
- MongoDB port-forwarded to localhost:27017

Usage:
    python3 scripts/utils/test-mongodb.py
"""

import sys
import os
import subprocess
import base64
from datetime import datetime
import json

try:
    import pymongo
    from pymongo import MongoClient
except ImportError:
    print("❌ Error: pymongo not installed")
    print("Please install it with: pip install pymongo")
    sys.exit(1)

def get_mongodb_credentials():
    """Get MongoDB credentials from Kubernetes secret"""
    try:
        # Get username
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'mongodb-credentials', 
            '-n', 'mongodb', '-o', 'jsonpath={.data.root-username}'
        ], capture_output=True, text=True, check=True)
        username = base64.b64decode(result.stdout).decode('utf-8')
        
        # Get password
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'mongodb-credentials', 
            '-n', 'mongodb', '-o', 'jsonpath={.data.root-password}'
        ], capture_output=True, text=True, check=True)
        password = base64.b64decode(result.stdout).decode('utf-8')
        
        # Get database
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'mongodb-credentials', 
            '-n', 'mongodb', '-o', 'jsonpath={.data.database}'
        ], capture_output=True, text=True, check=True)
        database = base64.b64decode(result.stdout).decode('utf-8')
        
        return username, password, database
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting credentials: {e}")
        return None, None, None
    except Exception as e:
        print(f"❌ Error decoding credentials: {e}")
        return None, None, None

def test_mongodb_connection():
    """Test MongoDB connection and perform CRUD operations"""
    print("🔍 MongoDB Connection Test")
    print("=" * 50)
    
    # Get credentials
    username, password, database = get_mongodb_credentials()
    if not all([username, password, database]):
        print("❌ Failed to get MongoDB credentials")
        return False
    
    print(f"📋 Connection Details:")
    print(f"   Host: localhost")
    print(f"   Port: 27017")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print(f"   Database: {database}")
    print()
    
    # Connection string
    connection_string = f"mongodb://{username}:{password}@localhost:27017/{database}?authSource=admin"
    print(f"🔗 Connection String:")
    print(f"   mongodb://{username}:{'*' * len(password)}@localhost:27017/{database}?authSource=admin")
    print()
    
    try:
        # Connect to MongoDB
        print("🔌 Connecting to MongoDB...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected successfully!")
        
        # Get database
        db = client[database]
        
        # Create test collection
        collection_name = "test_collection"
        collection = db[collection_name]
        
        print(f"\n📦 Creating test collection: {collection_name}")
        
        # Insert test documents
        test_documents = [
            {
                "name": "Test User 1",
                "email": "user1@example.com",
                "role": "admin",
                "created_at": datetime.now(),
                "metadata": {
                    "test_run": True,
                    "version": "1.0",
                    "platform": "nexus"
                }
            },
            {
                "name": "Test User 2",
                "email": "user2@example.com", 
                "role": "user",
                "created_at": datetime.now(),
                "metadata": {
                    "test_run": True,
                    "version": "1.0",
                    "platform": "nexus"
                }
            },
            {
                "name": "Test Service",
                "type": "microservice",
                "status": "running",
                "created_at": datetime.now(),
                "config": {
                    "port": 8080,
                    "replicas": 3,
                    "database": "mongodb"
                }
            }
        ]
        
        print(f"📝 Inserting {len(test_documents)} test documents...")
        result = collection.insert_many(test_documents)
        print(f"✅ Inserted documents with IDs: {[str(id) for id in result.inserted_ids]}")
        
        # Test queries
        print(f"\n🔍 Testing queries...")
        
        # Count documents
        count = collection.count_documents({})
        print(f"📊 Total documents in collection: {count}")
        
        # Find all users
        users = list(collection.find({"role": {"$exists": True}}))
        print(f"👥 Found {len(users)} user documents")
        
        # Find services
        services = list(collection.find({"type": "microservice"}))
        print(f"🔧 Found {len(services)} service documents")
        
        # Create index
        print(f"\n🔍 Creating index on 'email' field...")
        collection.create_index("email", unique=True)
        print("✅ Index created successfully")
        
        # List all collections
        print(f"\n📋 Available collections in database '{database}':")
        collections = db.list_collection_names()
        for coll in collections:
            doc_count = db[coll].count_documents({})
            print(f"   - {coll}: {doc_count} documents")
        
        # Database stats
        print(f"\n📊 Database Statistics:")
        stats = db.command("dbstats")
        print(f"   - Collections: {stats.get('collections', 'N/A')}")
        print(f"   - Data Size: {stats.get('dataSize', 0) / 1024:.2f} KB")
        print(f"   - Storage Size: {stats.get('storageSize', 0) / 1024:.2f} KB")
        print(f"   - Indexes: {stats.get('indexes', 'N/A')}")
        
        # MongoDB version
        server_info = client.server_info()
        print(f"\n🏷️  MongoDB Server Info:")
        print(f"   - Version: {server_info.get('version', 'Unknown')}")
        print(f"   - Git Version: {server_info.get('gitVersion', 'Unknown')}")
        
        print(f"\n✅ All tests completed successfully!")
        print(f"\n🎯 What to verify in MongoDB UI:")
        print(f"   1. Database '{database}' exists")
        print(f"   2. Collection '{collection_name}' has {len(test_documents)} documents")
        print(f"   3. Documents contain user and service data")
        print(f"   4. Index on 'email' field exists")
        print(f"   5. All documents have timestamps and metadata")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

def print_ui_connection_info():
    """Print information for connecting with UI tools"""
    username, password, database = get_mongodb_credentials()
    if not all([username, password, database]):
        return
        
    print("\n" + "=" * 60)
    print("📱 MongoDB UI Tool Connection Information")
    print("=" * 60)
    
    print(f"\n🔧 For MongoDB Compass:")
    print(f"   Connection String:")
    print(f"   mongodb://{username}:{password}@localhost:27017/{database}?authSource=admin")
    print(f"   ")
    print(f"   Or manually enter:")
    print(f"   - Host: localhost")
    print(f"   - Port: 27017")
    print(f"   - Username: {username}")
    print(f"   - Password: {password}")
    print(f"   - Authentication Database: admin")
    print(f"   - Default Database: {database}")
    
    print(f"\n🌐 For web-based tools (like Mongo Express):")
    print(f"   - MongoDB URL: mongodb://localhost:27017")
    print(f"   - Username: {username}")
    print(f"   - Password: {password}")
    print(f"   - Database: {database}")
    
    print(f"\n💻 For command line (mongosh):")
    print(f"   mongosh \"mongodb://{username}:{password}@localhost:27017/{database}?authSource=admin\"")
    
    print(f"\n📋 Test Collection to verify:")
    print(f"   - Database: {database}")
    print(f"   - Collection: test_collection")
    print(f"   - Expected: 3 documents with user and service data")

if __name__ == "__main__":
    print("🚀 MongoDB Test Script")
    print("=" * 50)
    
    # Check if port forwarding is active
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 27017))
        sock.close()
        if result != 0:
            print("⚠️  Warning: Port 27017 not accessible")
            print("   Make sure MongoDB port forwarding is active:")
            print("   bash scripts/deploy/platform-mongodb.sh --test-connection")
            print()
    except:
        pass
    
    # Run tests
    success = test_mongodb_connection()
    
    # Print UI connection info
    print_ui_connection_info()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"   You can now connect with MongoDB Compass or other UI tools")
        sys.exit(0)
    else:
        print(f"\n❌ Test failed!")
        sys.exit(1)
