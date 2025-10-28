#!/usr/bin/env python3
"""
Generate Postman collections for Database Orchestrator Services
"""

import json
import os
from datetime import datetime

def create_mongodb_collection():
    """Create MongoDB Orchestrator Postman collection"""
    
    collection = {
        "info": {
            "name": "Nexus MongoDB Orchestrator API",
            "description": "Complete API collection for MongoDB Orchestrator Service",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{mongodb_orchestrator_url}}/health",
                        "host": ["{{mongodb_orchestrator_url}}"],
                        "path": ["health"]
                    }
                }
            },
            {
                "name": "MongoDB Operations",
                "item": [
                    {
                        "name": "Create Collection",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "create_collection"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Insert Document",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "insert",
                                    "data": {
                                        "name": "John Doe",
                                        "email": "john@example.com",
                                        "age": 30,
                                        "created_at": "2024-01-01T00:00:00Z"
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Find Documents",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "find",
                                    "query": {
                                        "email": "john@example.com"
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Find One Document",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "find_one",
                                    "query": {
                                        "email": "john@example.com"
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Update Documents",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "update",
                                    "query": {
                                        "email": "john@example.com"
                                    },
                                    "update": {
                                        "$set": {
                                            "last_login": "2024-01-02T00:00:00Z",
                                            "status": "active"
                                        }
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Delete Documents",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "collection_name": "users",
                                    "operation": "delete",
                                    "query": {
                                        "email": "john@example.com"
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/operation",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "operation"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Database Management",
                "item": [
                    {
                        "name": "List Collections",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/collections/test-service/testdb",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "collections", "test-service", "testdb"]
                            }
                        }
                    },
                    {
                        "name": "List Databases",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{mongodb_orchestrator_url}}/api/mongodb/databases/test-service",
                                "host": ["{{mongodb_orchestrator_url}}"],
                                "path": ["api", "mongodb", "databases", "test-service"]
                            }
                        }
                    }
                ]
            }
        ],
        "variable": [
            {
                "key": "mongodb_orchestrator_url",
                "value": "http://localhost:8001",
                "type": "string"
            }
        ]
    }
    
    return collection

def create_postgresql_collection():
    """Create PostgreSQL Orchestrator Postman collection"""
    
    collection = {
        "info": {
            "name": "Nexus PostgreSQL Orchestrator API",
            "description": "Complete API collection for PostgreSQL Orchestrator Service",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{postgresql_orchestrator_url}}/health",
                        "host": ["{{postgresql_orchestrator_url}}"],
                        "path": ["health"]
                    }
                }
            },
            {
                "name": "PostgreSQL Operations",
                "item": [
                    {
                        "name": "Create Table",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "create_table",
                                    "data": {
                                        "id": "SERIAL PRIMARY KEY",
                                        "name": "VARCHAR(255) NOT NULL",
                                        "email": "VARCHAR(255) UNIQUE NOT NULL",
                                        "age": "INTEGER",
                                        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Insert Record",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "insert",
                                    "columns": ["name", "email", "age"],
                                    "data": {
                                        "name": "Jane Doe",
                                        "email": "jane@example.com",
                                        "age": 25
                                    }
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Select All Records",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "select"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Select with Query",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "select",
                                    "query": "SELECT * FROM test-service_testdb.users WHERE email = $1",
                                    "params": ["jane@example.com"]
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Update Records",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "update",
                                    "query": "email = $1",
                                    "data": {
                                        "age": 26,
                                        "status": "active"
                                    },
                                    "params": ["jane@example.com"]
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    },
                    {
                        "name": "Delete Records",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "test-service",
                                    "database_name": "testdb",
                                    "table_name": "users",
                                    "operation": "delete",
                                    "query": "email = $1",
                                    "params": ["jane@example.com"]
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/operation",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "operation"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Database Management",
                "item": [
                    {
                        "name": "Create Database",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "service_name": "user-service",
                                    "database_name": "users",
                                    "description": "User management database"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/database",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "database"]
                            }
                        }
                    },
                    {
                        "name": "List Databases",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/databases/user-service",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "databases", "user-service"]
                            }
                        }
                    },
                    {
                        "name": "List Tables",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/tables/test-service/testdb",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "tables", "test-service", "testdb"]
                            }
                        }
                    },
                    {
                        "name": "List Schemas",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{postgresql_orchestrator_url}}/api/postgresql/schemas/test-service",
                                "host": ["{{postgresql_orchestrator_url}}"],
                                "path": ["api", "postgresql", "schemas", "test-service"]
                            }
                        }
                    }
                ]
            }
        ],
        "variable": [
            {
                "key": "postgresql_orchestrator_url",
                "value": "http://localhost:8002",
                "type": "string"
            }
        ]
    }
    
    return collection

def create_environment():
    """Create Postman environment"""
    
    environment = {
        "id": "nexus-database-env",
        "name": "Nexus Database Orchestrator Environment",
        "values": [
            {
                "key": "mongodb_orchestrator_url",
                "value": "http://localhost:8001",
                "type": "default",
                "enabled": True
            },
            {
                "key": "postgresql_orchestrator_url",
                "value": "http://localhost:8002",
                "type": "default",
                "enabled": True
            },
            {
                "key": "mongodb_direct_url",
                "value": "mongodb://admin:adminpass123@localhost:27017",
                "type": "default",
                "enabled": True
            },
            {
                "key": "postgresql_direct_url",
                "value": "postgresql://postgres:password@localhost:5432/postgres",
                "type": "default",
                "enabled": True
            }
        ],
        "_postman_variable_scope": "environment"
    }
    
    return environment

def main():
    """Generate all Postman files"""
    
    # Create output directory
    output_dir = "postman-collections"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate collections
    mongodb_collection = create_mongodb_collection()
    postgresql_collection = create_postgresql_collection()
    environment = create_environment()
    
    # Save files
    with open(f"{output_dir}/nexus_mongodb_orchestrator_collection.json", "w") as f:
        json.dump(mongodb_collection, f, indent=2)
    
    with open(f"{output_dir}/nexus_postgresql_orchestrator_collection.json", "w") as f:
        json.dump(postgresql_collection, f, indent=2)
    
    with open(f"{output_dir}/nexus_database_environment.json", "w") as f:
        json.dump(environment, f, indent=2)
    
    print("✅ Postman collections generated successfully!")
    print(f"📁 Files saved in: {output_dir}/")
    print("📋 Collections:")
    print("   - nexus_mongodb_orchestrator_collection.json")
    print("   - nexus_postgresql_orchestrator_collection.json")
    print("   - nexus_database_environment.json")

if __name__ == "__main__":
    main()
