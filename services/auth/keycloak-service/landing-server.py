#!/usr/bin/env python3
"""
Simple HTTP server for the Nexus Platform landing page
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

class LandingPageHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server(port=8082):
    server_address = ('', port)
    httpd = HTTPServer(server_address, LandingPageHandler)
    print(f"🚀 Landing page server running on http://localhost:{port}")
    print(f"📄 Login page: http://localhost:{port}/login.html")
    print(f"🏠 Landing page: http://localhost:{port}/landing-page.html")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
    run_server(port)
