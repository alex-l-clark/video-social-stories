#!/usr/bin/env python3
"""
Debug script to capture and analyze API calls from the frontend.
This will help us understand what endpoints the frontend is actually trying to call.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import time
import re
from urllib.error import HTTPError

FRONTEND_PORT = 3002
BACKEND_URL = "http://localhost:8000"

class DebugProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="social_story_frontend/dist", **kwargs)
    
    def log_message(self, format, *args):
        """Override to add timestamps to logs"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")
    
    def do_POST(self):
        print(f"\n🔍 POST Request Received:")
        print(f"   Path: {self.path}")
        print(f"   Headers: {dict(self.headers)}")
        
        # Read the request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None
        
        if post_data:
            try:
                body_json = json.loads(post_data.decode('utf-8'))
                print(f"   Body: {json.dumps(body_json, indent=2)}")
            except:
                print(f"   Body: {post_data}")
        
        # Check if this looks like an API call
        if self.path.startswith('/api/') or self.path.startswith('/v1/') or 'api' in self.path.lower():
            print(f"   🎯 This looks like an API call!")
            self.proxy_to_backend(post_data)
        else:
            print(f"   ❓ This doesn't look like an API call, sending 404")
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "error": f"Unknown endpoint: {self.path}",
                "suggestion": "Try endpoints like /api/v1/social-story:start or /v1/social-story:start"
            }).encode()
            self.wfile.write(error_response)
    
    def do_GET(self):
        if self.path.startswith('/api/') or self.path.startswith('/v1/'):
            print(f"\n🔍 GET Request to API endpoint:")
            print(f"   Path: {self.path}")
            self.proxy_to_backend()
        else:
            super().do_GET()
    
    def do_OPTIONS(self):
        print(f"\n🔍 OPTIONS Request (CORS preflight):")
        print(f"   Path: {self.path}")
        print(f"   Headers: {dict(self.headers)}")
        
        # Always allow CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
        print(f"   ✅ Sent CORS preflight response")
    
    def proxy_to_backend(self, post_data=None):
        try:
            # Build backend URL - try different mappings
            # For the exact endpoint we know the frontend is calling
            if self.path == '/v1/social-story:start':
                possible_paths = ['/v1/social-story:start']  # Direct mapping for known endpoint
            else:
                possible_paths = [
                    self.path,  # Direct mapping
                    self.path.replace('/api', ''),  # Remove /api prefix  
                    f"/v1{self.path}" if not self.path.startswith('/v1') else self.path,  # Add v1 prefix
                    self.path.replace('/api/v1', '/v1'),  # Replace /api/v1 with /v1
                    self.path.replace('/generate', '/social-story:start'),  # Map generate to social-story:start
                    self.path.replace('/create', '/social-story:start'),  # Map create to social-story:start
                    self.path.replace('/social-story', '/social-story:start'),  # Add :start suffix
                ]
            
            for backend_path in possible_paths:
                backend_url = f"{BACKEND_URL}{backend_path}"
                print(f"   🚀 Trying: {backend_url}")
                
                try:
                    # Create request to backend
                    req = urllib.request.Request(backend_url, data=post_data, method=self.command)
                    
                    # Copy relevant headers
                    for header, value in self.headers.items():
                        if header.lower() not in ['host', 'content-length', 'origin']:
                            req.add_header(header, value)
                    
                    # Make request to backend
                    with urllib.request.urlopen(req, timeout=10) as response:
                        print(f"   ✅ SUCCESS with {backend_url}!")
                        
                        # Send response back to frontend
                        self.send_response(response.status)
                        
                        # Copy response headers
                        for header, value in response.headers.items():
                            if header.lower() != 'content-length':
                                self.send_header(header, value)
                        
                        # Add CORS headers
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                        
                        # Read and send response body
                        response_data = response.read()
                        self.send_header('Content-Length', str(len(response_data)))
                        self.end_headers()
                        self.wfile.write(response_data)
                        
                        # Log response
                        try:
                            response_json = json.loads(response_data.decode('utf-8'))
                            print(f"   📤 Response: {json.dumps(response_json, indent=2)}")
                        except:
                            print(f"   📤 Response: {response_data}")
                        
                        return  # Success, exit the loop
                        
                except HTTPError as e:
                    print(f"   ❌ HTTP Error with {backend_url}: {e.code} - {e.reason}")
                    if e.code != 404:  # If it's not a 404, return this error
                        self.send_response(e.code)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(e.read())
                        return
                except Exception as e:
                    print(f"   ⚠️  Error with {backend_url}: {e}")
                    continue
            
            # If we get here, all attempts failed
            print(f"   ❌ All backend attempts failed!")
            self.send_response(502)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "error": "Backend unavailable",
                "attempted_urls": [f"{BACKEND_URL}{p}" for p in possible_paths]
            }).encode()
            self.wfile.write(error_response)
                
        except Exception as e:
            print(f"   💥 Unexpected error: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"error": f"Proxy error: {str(e)}"}).encode()
            self.wfile.write(error_response)

if __name__ == "__main__":
    with socketserver.TCPServer(("", FRONTEND_PORT), DebugProxyHTTPRequestHandler) as httpd:
        print(f"🔍 DEBUG PROXY SERVER running at http://localhost:{FRONTEND_PORT}")
        print(f"📁 Serving frontend files from social_story_frontend/dist/")
        print(f"🔄 Proxying API calls to {BACKEND_URL}")
        print(f"📊 Will log ALL API requests in detail")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Debug proxy server stopped")
