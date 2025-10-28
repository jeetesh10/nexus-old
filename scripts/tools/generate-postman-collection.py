#!/usr/bin/env python3
"""
Postman Collection Generator for Nexus Platform
Automatically generates Postman collections from OpenAPI specifications
"""

import json
import yaml
import os
import sys
from datetime import datetime
from pathlib import Path

class PostmanCollectionGenerator:
    def __init__(self, openapi_file, output_dir="postman-collections"):
        self.openapi_file = openapi_file
        self.output_dir = output_dir
        self.openapi_spec = None
        self.collection = None
        
    def load_openapi_spec(self):
        """Load OpenAPI specification from file"""
        try:
            with open(self.openapi_file, 'r', encoding='utf-8') as f:
                if self.openapi_file.endswith('.yaml') or self.openapi_file.endswith('.yml'):
                    self.openapi_spec = yaml.safe_load(f)
                else:
                    self.openapi_spec = json.load(f)
            print(f"✅ Loaded OpenAPI spec from {self.openapi_file}")
        except Exception as e:
            print(f"❌ Error loading OpenAPI spec: {e}")
            sys.exit(1)
    
    def create_collection_structure(self):
        """Create basic Postman collection structure"""
        info = self.openapi_spec.get('info', {})
        
        self.collection = {
            "info": {
                "name": f"{info.get('title', 'Nexus Platform API')} - Postman Collection",
                "description": info.get('description', 'Auto-generated Postman collection'),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "version": info.get('version', '1.0.0'),
                "updatedAt": datetime.now().isoformat()
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "{{base_url}}",
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string"
                },
                {
                    "key": "refresh_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": [],
            "event": [
                {
                    "listen": "prerequest",
                    "script": {
                        "type": "text/javascript",
                        "exec": [
                            "// Set common headers",
                            "pm.request.headers.add({",
                            "    key: 'Content-Type',",
                            "    value: 'application/json'",
                            "});",
                            "",
                            "// Add request ID for tracking",
                            "pm.request.headers.add({",
                            "    key: 'X-Request-ID',",
                            "    value: pm.variables.replaceIn('{{$guid}}')",
                            "});",
                            "",
                            "// Add authentication token if available",
                            "if (pm.environment.get('access_token')) {",
                            "    pm.request.headers.add({",
                            "        key: 'Authorization',",
                            "        value: 'Bearer ' + pm.environment.get('access_token')",
                            "    });",
                            "}"
                        ]
                    }
                }
            ]
        }
    
    def create_folder_structure(self):
        """Create folder structure based on tags"""
        folders = {}
        
        for path, path_item in self.openapi_spec.get('paths', {}).items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    tags = operation.get('tags', ['Other'])
                    for tag in tags:
                        if tag not in folders:
                            folders[tag] = []
                        folders[tag].append({
                            'path': path,
                            'method': method.upper(),
                            'operation': operation
                        })
        
        return folders
    
    def create_request_item(self, path, method, operation):
        """Create a Postman request item"""
        operation_id = operation.get('operationId', f"{method.lower()}_{path.replace('/', '_').replace('-', '_')}")
        summary = operation.get('summary', operation_id)
        description = operation.get('description', '')
        
        # Build URL
        url = f"{{{{base_url}}}}{path}"
        
        # Handle query parameters
        query_params = []
        for param in operation.get('parameters', []):
            if param.get('in') == 'query':
                query_params.append({
                    "key": param['name'],
                    "value": param.get('example', ''),
                    "description": param.get('description', ''),
                    "disabled": not param.get('required', False)
                })
        
        # Handle request body
        request_body = None
        if 'requestBody' in operation:
            content = operation['requestBody'].get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                examples = content['application/json'].get('examples', {})
                
                # Get example from schema or examples
                example_body = {}
                if examples:
                    # Use first example
                    first_example = list(examples.values())[0]
                    example_body = first_example.get('value', {})
                elif schema.get('$ref'):
                    # Reference to schema
                    schema_name = schema['$ref'].split('/')[-1]
                    example_body = self.get_schema_example(schema_name)
                
                if example_body:
                    request_body = {
                        "mode": "raw",
                        "raw": json.dumps(example_body, indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
        
        # Create request
        request = {
            "name": summary,
            "request": {
                "method": method,
                "header": [],
                "url": {
                    "raw": url,
                    "host": ["{{base_url}}"],
                    "path": path.strip('/').split('/'),
                    "query": query_params
                }
            },
            "response": []
        }
        
        if request_body:
            request["request"]["body"] = request_body
        
        # Add description
        if description:
            request["description"] = description
        
        return request
    
    def get_schema_example(self, schema_name):
        """Get example from schema definition"""
        schemas = self.openapi_spec.get('components', {}).get('schemas', {})
        if schema_name in schemas:
            schema = schemas[schema_name]
            example = {}
            for prop_name, prop_def in schema.get('properties', {}).items():
                if 'example' in prop_def:
                    example[prop_name] = prop_def['example']
                elif prop_def.get('type') == 'string':
                    example[prop_name] = f"example_{prop_name}"
                elif prop_def.get('type') == 'integer':
                    example[prop_name] = 0
                elif prop_def.get('type') == 'boolean':
                    example[prop_name] = False
                elif prop_def.get('type') == 'array':
                    example[prop_name] = []
            return example
        return {}
    
    def create_test_scripts(self, operation):
        """Create test scripts for the request"""
        tests = []
        
        # Basic status code test
        tests.append("// Validate response status")
        tests.append("pm.test('Status code is 200', function () {")
        tests.append("    pm.response.to.have.status(200);")
        tests.append("});")
        tests.append("")
        
        # Response time test
        tests.append("// Validate response time")
        tests.append("pm.test('Response time is less than 200ms', function () {")
        tests.append("    pm.expect(pm.response.responseTime).to.be.below(200);")
        tests.append("});")
        tests.append("")
        
        # Response structure test
        responses = operation.get('responses', {})
        if '200' in responses:
            content = responses['200'].get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                if schema.get('$ref'):
                    schema_name = schema['$ref'].split('/')[-1]
                    tests.extend(self.create_schema_validation_tests(schema_name))
        
        # Token handling for authentication endpoints
        if 'login' in operation.get('operationId', '').lower():
            tests.append("// Store tokens for subsequent requests")
            tests.append("if (pm.response.code === 200) {")
            tests.append("    const jsonData = pm.response.json();")
            tests.append("    if (jsonData.access_token) {")
            tests.append("        pm.environment.set('access_token', jsonData.access_token);")
            tests.append("    }")
            tests.append("    if (jsonData.refresh_token) {")
            tests.append("        pm.environment.set('refresh_token', jsonData.refresh_token);")
            tests.append("    }")
            tests.append("}")
        
        return tests
    
    def create_schema_validation_tests(self, schema_name):
        """Create validation tests for schema"""
        tests = []
        schemas = self.openapi_spec.get('components', {}).get('schemas', {})
        
        if schema_name in schemas:
            schema = schemas[schema_name]
            tests.append("// Validate response structure")
            tests.append("pm.test('Response has required fields', function () {")
            tests.append("    const jsonData = pm.response.json();")
            
            for prop_name, prop_def in schema.get('properties', {}).items():
                tests.append(f"    pm.expect(jsonData).to.have.property('{prop_name}');")
            
            tests.append("});")
            tests.append("")
        
        return tests
    
    def generate_collection(self):
        """Generate the complete Postman collection"""
        self.load_openapi_spec()
        self.create_collection_structure()
        
        # Create folder structure
        folders = self.create_folder_structure()
        
        # Add folders to collection
        for folder_name, requests in folders.items():
            folder = {
                "name": folder_name,
                "item": []
            }
            
            for req in requests:
                request_item = self.create_request_item(
                    req['path'], 
                    req['method'], 
                    req['operation']
                )
                
                # Add test scripts
                test_scripts = self.create_test_scripts(req['operation'])
                if test_scripts:
                    request_item["event"] = [
                        {
                            "listen": "test",
                            "script": {
                                "type": "text/javascript",
                                "exec": test_scripts
                            }
                        }
                    ]
                
                folder["item"].append(request_item)
            
            self.collection["item"].append(folder)
        
        return self.collection
    
    def save_collection(self, collection, filename=None):
        """Save collection to file"""
        if not filename:
            info = self.openapi_spec.get('info', {})
            title = info.get('title', 'Nexus Platform API').replace(' ', '_').lower()
            filename = f"{title}_postman_collection.json"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Postman collection saved to {filepath}")
        return filepath

def create_environment_files(output_dir):
    """Create Postman environment files"""
    environments = {
        "development": {
            "name": "Nexus Platform - Development",
            "values": [
                {"key": "base_url", "value": "http://localhost:8084/api/auth", "enabled": True},
                {"key": "auth_url", "value": "http://localhost:8084", "enabled": True},
                {"key": "admin_url", "value": "http://localhost:8081", "enabled": True},
                {"key": "access_control_url", "value": "http://localhost:8083", "enabled": True},
                {"key": "access_token", "value": "", "enabled": True},
                {"key": "refresh_token", "value": "", "enabled": True}
            ]
        },
        "staging": {
            "name": "Nexus Platform - Staging",
            "values": [
                {"key": "base_url", "value": "https://staging-auth.nexus.platform/api/auth", "enabled": True},
                {"key": "auth_url", "value": "https://staging-auth.nexus.platform", "enabled": True},
                {"key": "admin_url", "value": "https://staging-admin.nexus.platform", "enabled": True},
                {"key": "access_control_url", "value": "https://staging-access.nexus.platform", "enabled": True},
                {"key": "access_token", "value": "", "enabled": True},
                {"key": "refresh_token", "value": "", "enabled": True}
            ]
        },
        "production": {
            "name": "Nexus Platform - Production",
            "values": [
                {"key": "base_url", "value": "https://auth.nexus.platform/api/auth", "enabled": True},
                {"key": "auth_url", "value": "https://auth.nexus.platform", "enabled": True},
                {"key": "admin_url", "value": "https://admin.nexus.platform", "enabled": True},
                {"key": "access_control_url", "value": "https://access.nexus.platform", "enabled": True},
                {"key": "access_token", "value": "", "enabled": True},
                {"key": "refresh_token", "value": "", "enabled": True}
            ]
        }
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    for env_name, env_data in environments.items():
        filename = f"nexus_platform_{env_name}_environment.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(env_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Environment file saved to {filepath}")

def create_test_documentation(openapi_file, output_dir):
    """Create test documentation from OpenAPI spec"""
    try:
        with open(openapi_file, 'r', encoding='utf-8') as f:
            if openapi_file.endswith('.yaml') or openapi_file.endswith('.yml'):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)
    except Exception as e:
        print(f"❌ Error loading OpenAPI spec for documentation: {e}")
        return
    
    test_cases = []
    tc_number = 1
    
    for path, path_item in spec.get('paths', {}).items():
        for method, operation in path_item.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                operation_id = operation.get('operationId', f"{method.lower()}_{path.replace('/', '_')}")
                summary = operation.get('summary', operation_id)
                description = operation.get('description', '')
                
                # Create test case
                test_case = f"""## Test Case: [TC-{tc_number:03d}] {summary}

### **Objective**
{description}

### **Prerequisites**
- Auth API service is running
- Valid test data available
- Network connectivity established

### **Test Steps**
1. **Send {method.upper()} Request**
   - Method: {method.upper()}
   - URL: `{{{{base_url}}}}{path}`
   - Headers: `Content-Type: application/json`
   - Body: Request payload (if applicable)

2. **Validate Response**
   - Status Code: Check expected status code
   - Response Structure: Validate response format
   - Data Validation: Verify response data

### **Expected Results**
- **Status Code**: Expected HTTP status code
- **Response Body**: Valid response structure
- **Performance**: Response time < 200ms

### **Test Data**
```json
{{
  // Test data will be populated from examples
}}
```

### **Expected Response**
```json
{{
  // Expected response structure
}}
```

### **Validation Rules**
- [ ] Status code matches expected
- [ ] Response structure is valid
- [ ] Response time is acceptable
- [ ] Error handling works correctly

### **Cleanup**
- No cleanup required (stateless operation)

---
"""
                test_cases.append(test_case)
                tc_number += 1
    
    # Save test documentation
    os.makedirs(output_dir, exist_ok=True)
    doc_file = os.path.join(output_dir, "API_TEST_CASES.md")
    
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write("# API Test Cases - Nexus Platform\n\n")
        f.write("This document contains test cases for all API endpoints.\n\n")
        f.write("## Test Cases\n\n")
        f.writelines(test_cases)
    
    print(f"✅ Test documentation saved to {doc_file}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python generate-postman-collection.py <openapi_file> [output_dir]")
        print("Example: python generate-postman-collection.py services/auth/auth-api-service/openapi.yaml")
        sys.exit(1)
    
    openapi_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "postman-collections"
    
    if not os.path.exists(openapi_file):
        print(f"❌ OpenAPI file not found: {openapi_file}")
        sys.exit(1)
    
    print(f"🚀 Generating Postman collection from {openapi_file}")
    
    # Generate collection
    generator = PostmanCollectionGenerator(openapi_file, output_dir)
    collection = generator.generate_collection()
    
    # Save collection
    collection_file = generator.save_collection(collection)
    
    # Create environment files
    create_environment_files(output_dir)
    
    # Create test documentation
    create_test_documentation(openapi_file, output_dir)
    
    print("\n🎉 Postman collection generation completed!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Collection file: {collection_file}")
    print("\n📋 Next Steps:")
    print("1. Import the collection file into Postman")
    print("2. Import the environment files for different stages")
    print("3. Review and update test cases as needed")
    print("4. Run the test suite to validate API functionality")

if __name__ == "__main__":
    main()
