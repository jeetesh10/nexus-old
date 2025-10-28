#!/usr/bin/env python3
"""
API Server for dynamic service-group mappings
"""
import sqlite3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'services.db')
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/api/services':
                self.get_services()
            elif path == '/api/user-access':
                user_groups = query_params.get('groups', [None])[0]
                if user_groups:
                    user_groups = user_groups.split(',')
                self.get_user_access(user_groups)
            elif path == '/api/health':
                self.get_health()
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_services(self):
        """Get all services"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT service_id, title, description, icon, url, status
                FROM services
                ORDER BY service_id
            """)
            
            services = []
            for row in cursor.fetchall():
                services.append(dict(row))
            
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(services).encode())
            
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            self.send_error(500, f"Database error: {str(e)}")
    
    def get_user_access(self, user_groups):
        """Get user's accessible services based on groups"""
        try:
            if not user_groups:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps([]).encode())
                return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get services accessible to user based on their groups
            placeholders = ','.join(['?' for _ in user_groups])
            cursor.execute(f"""
                SELECT DISTINCT 
                    s.service_id, 
                    s.title, 
                    s.description, 
                    s.icon, 
                    s.url, 
                    s.status,
                    sgm.access_level
                FROM services s
                JOIN service_group_mappings sgm ON s.id = sgm.service_id
                JOIN groups g ON sgm.group_id = g.id
                WHERE g.group_path IN ({placeholders})
                AND g.is_active = 1
                ORDER BY s.service_id
            """, user_groups)
            
            accessible_services = []
            for row in cursor.fetchall():
                accessible_services.append(dict(row))
            
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(accessible_services).encode())
            
        except Exception as e:
            logger.error(f"Error getting user access: {e}")
            self.send_error(500, f"Database error: {str(e)}")
    
    def get_health(self):
        """Health check endpoint"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM services")
            service_count = cursor.fetchone()[0]
            conn.close()
            
            health_data = {
                "status": "healthy",
                "database": "connected",
                "services_count": service_count
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.send_error(500, f"Health check failed: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

def init_database():
    """Initialize the database with schema and default data"""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'services.db')
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Read and execute schema
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema (SQLite doesn't support multiple statements in execute)
    statements = schema.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            cursor.execute(statement)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def run_server(port=8083):
    """Run the API server"""
    try:
        # Initialize database
        init_database()
        
        # Start server
        server_address = ('', port)
        httpd = HTTPServer(server_address, ServiceAPIHandler)
        logger.info(f"API Server running on port {port}")
        logger.info(f"Health check: http://localhost:{port}/api/health")
        logger.info(f"Services: http://localhost:{port}/api/services")
        logger.info(f"User access: http://localhost:{port}/api/user-access?groups=nexus,platform-admin")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    run_server()
