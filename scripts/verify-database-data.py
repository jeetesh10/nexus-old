#!/usr/bin/env python3
"""
Verify data in both PostgreSQL and MongoDB databases
"""

import asyncio
import asyncpg
import httpx
import json

async def verify_postgresql_data():
    """Verify PostgreSQL data directly"""
    print("🗄️  PostgreSQL Database Verification")
    print("=" * 50)
    
    try:
        # Connect directly to PostgreSQL
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='password',
            database='postgres'
        )
        
        # Check if schema exists
        schemas = await conn.fetch("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'test_service_%'
        """)
        
        print(f"📋 Found schemas: {[s['schema_name'] for s in schemas]}")
        
        if schemas:
            schema_name = schemas[0]['schema_name']
            print(f"🔍 Checking schema: {schema_name}")
            
            # Check tables in schema
            tables = await conn.fetch(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = $1
            """, schema_name)
            
            print(f"📊 Tables in {schema_name}: {[t['table_name'] for t in tables]}")
            
            if tables:
                table_name = tables[0]['table_name']
                print(f"📝 Checking table: {table_name}")
                
                # Get table structure
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                """, schema_name, table_name)
                
                print(f"🏗️  Table structure:")
                for col in columns:
                    print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                
                # Get data
                data = await conn.fetch(f'SELECT * FROM "{schema_name}".{table_name}')
                print(f"📊 Data in table:")
                for row in data:
                    print(f"   - {dict(row)}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL verification failed: {e}")

async def verify_postgresql_orchestrator():
    """Verify PostgreSQL orchestrator API"""
    print("\n🔧 PostgreSQL Orchestrator API Verification")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            # Health check
            response = await client.get("http://localhost:8002/health")
            print(f"🏥 Health: {response.json()}")
            
            # List tables
            response = await client.get("http://localhost:8002/api/postgresql/tables/test-service/testdb")
            print(f"📋 Tables: {response.json()}")
            
            # Select data
            response = await client.post(
                "http://localhost:8002/api/postgresql/operation",
                json={
                    "service_name": "test-service",
                    "database_name": "testdb",
                    "table_name": "users",
                    "operation": "select"
                }
            )
            print(f"📊 Data via API: {response.json()}")
            
    except Exception as e:
        print(f"❌ PostgreSQL orchestrator verification failed: {e}")

async def verify_mongodb_orchestrator():
    """Verify MongoDB orchestrator API"""
    print("\n🔧 MongoDB Orchestrator API Verification")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            # Health check
            response = await client.get("http://localhost:8001/health")
            print(f"🏥 Health: {response.json()}")
            
    except Exception as e:
        print(f"❌ MongoDB orchestrator verification failed: {e}")

async def main():
    """Run all verifications"""
    print("🔍 Database Verification Report")
    print("=" * 60)
    
    await verify_postgresql_data()
    await verify_postgresql_orchestrator()
    await verify_mongodb_orchestrator()
    
    print("\n" + "=" * 60)
    print("✅ Verification complete!")

if __name__ == "__main__":
    asyncio.run(main())
