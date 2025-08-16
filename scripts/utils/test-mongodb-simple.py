#!/usr/bin/env python3
"""
Simple MongoDB Connection Test
==============================

This script provides a basic automated test to verify MongoDB connectivity
without requiring a UI tool.

Requirements: pip install pymongo
"""

import subprocess
import base64
import json
from datetime import datetime

def get_credentials():
    """Get MongoDB credentials from kubectl"""
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
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None, None, None

def test_with_pymongo():
    """Test MongoDB using pymongo if available"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        username, password, database = get_credentials()
        if not username:
            return False
            
        connection_string = f"mongodb://{username}:{password}@localhost:27017/{database}?authSource=admin"
        
        print("🔌 Testing with pymongo...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database
        db = client[database]
        
        # Insert test document
        collection = db.test_collection
        test_doc = {
            "test": "automated_pymongo_test",
            "timestamp": datetime.now(),
            "success": True
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Document inserted with ID: {result.inserted_id}")
        
        # Query document
        found_doc = collection.find_one({"test": "automated_pymongo_test"})
        if found_doc:
            print("✅ Document retrieved successfully")
            print(f"   Document: {found_doc}")
        
        # Get count
        count = collection.count_documents({})
        print(f"✅ Total documents in collection: {count}")
        
        client.close()
        return True
        
    except ImportError:
        print("❌ pymongo not installed (pip install pymongo)")
        return False
    except Exception as e:
        print(f"❌ pymongo test failed: {e}")
        return False

def test_with_mongosh():
    """Test MongoDB using mongosh via kubectl"""
    try:
        username, password, database = get_credentials()
        if not username:
            return False
            
        print("🔌 Testing with kubectl + mongosh...")
        
        # Test basic connection
        test_script = f'''
        db = connect("mongodb://{username}:{password}@localhost:27017/{database}?authSource=admin");
        
        print("=== Connection Test ===");
        var pingResult = db.adminCommand("ping");
        print("Ping result:", JSON.stringify(pingResult));
        
        print("=== Insert Test Document ===");
        var testDoc = {{
            test: "automated_mongosh_test",
            timestamp: new Date(),
            success: true,
            method: "kubectl_mongosh"
        }};
        
        var insertResult = db.test_collection.insertOne(testDoc);
        print("Insert result:", JSON.stringify(insertResult));
        
        print("=== Query Test ===");
        var foundDoc = db.test_collection.findOne({{test: "automated_mongosh_test"}});
        print("Found document:", JSON.stringify(foundDoc, null, 2));
        
        print("=== Collection Stats ===");
        var count = db.test_collection.countDocuments({{}});
        print("Total documents:", count);
        
        var collections = db.getCollectionNames();
        print("Collections:", JSON.stringify(collections));
        '''
        
        # Execute via kubectl
        result = subprocess.run([
            'kubectl', 'exec', '-n', 'mongodb', 'mongodb-0', '--',
            'mongosh', '--quiet', '--eval', test_script
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ mongosh test successful!")
            print("Output:")
            print(result.stdout)
            return True
        else:
            print("❌ mongosh test failed!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ mongosh test failed: {e}")
        return False

def main():
    print("🚀 MongoDB Connection Test")
    print("=" * 50)
    
    username, password, database = get_credentials()
    if not username:
        print("❌ Could not get MongoDB credentials")
        return False
    
    print(f"📋 Connection Info:")
    print(f"   Host: localhost:27017")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print(f"   Database: {database}")
    print()
    
    # Try pymongo first
    pymongo_success = test_with_pymongo()
    print()
    
    # Try mongosh as fallback
    mongosh_success = test_with_mongosh()
    print()
    
    if pymongo_success or mongosh_success:
        print("🎉 MongoDB testing completed successfully!")
        print("   You can now use UI tools for manual verification")
        print("   or proceed with committing the deployment")
        return True
    else:
        print("❌ All automated tests failed")
        print("   Try manual testing with MongoDB Compass")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
