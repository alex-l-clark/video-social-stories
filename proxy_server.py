#!/usr/bin/env python3
"""
Simple proxy server to help debug frontend-backend communication.
This serves the frontend and proxies API calls to the backend.
Also injects a small runtime script that rewrites any requests to
https://api.example.com (or .dev) into relative paths so they go through the proxy.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from urllib.error import HTTPError

FRONTEND_PORT = 3001
BACKEND_URL = "http://localhost:8000"

DIST_DIR = "social_story_frontend/dist"
INDEX_PATH = os.path.join(DIST_DIR, "index.html")

INJECT_SCRIPT = (
    "<script>\n"
    "(function(){\n"
    "  function toRelative(u){\n"
    "    try {\n"
    "      var url = new URL(u, window.location.origin);\n"
    "      var isApiExample = (url.hostname === 'api.example.com' || url.hostname === 'api.example.dev');\n"
    "      var isLocal3002 = ((url.hostname === 'localhost' || url.hostname === '127.0.0.1') && url.port === '3002');\n"
    "      if ((isApiExample || isLocal3002) && (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/api/'))) {\n"
    "        return url.pathname + url.search + url.hash;\n"
    "      }\n"
    "      return u;\n"
    "    } catch (e) { return u; }\n"
    "  }\n"
    "  var originalFetch = window.fetch;\n"
    "  window.fetch = function(input, init){\n"
    "    if (typeof input === 'string') { input = toRelative(input); }\n"
    "    else if (input && input.url) { var r = toRelative(input.url); if (r !== input.url) { input = new Request(r, input); } }\n"
    "    return originalFetch.apply(this, arguments);\n"
    "  };\n"
    "  var origOpen = XMLHttpRequest.prototype.open;\n"
    "  XMLHttpRequest.prototype.open = function(method, url){\n"
    "    url = toRelative(url);\n"
    "    var rest = Array.prototype.slice.call(arguments, 2);\n"
    "    return origOpen.apply(this, [method, url].concat(rest));\n"
    "  };\n"
    "})();\n"
    "</script>"
)

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    
    def do_GET(self):
        # Proxy API GET requests
        if self.path.startswith('/api/') or self.path.startswith('/v1/'):
            return self.proxy_to_backend()

        # Inject runtime patch into index.html
        if self.path == '/' or self.path == '/index.html':
            try:
                with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
                if '</body>' in content:
                    content = content.replace('</body>', INJECT_SCRIPT + '\n</body>')
                else:
                    content += INJECT_SCRIPT
                data = content.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception as e:
                print(f"❌ Failed to serve injected index.html: {e}")
                # Fallback to default behavior
                return super().do_GET()

        return super().do_GET()
    
    def do_POST(self):
        # Handle API requests by proxying to backend
        if self.path.startswith('/api/') or self.path.startswith('/v1/'):
            self.proxy_to_backend()
        else:
            super().do_POST()
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        if self.path.startswith('/api/') or self.path.startswith('/v1/'):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        else:
            super().do_OPTIONS()
    
    def proxy_to_backend(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Build backend URL
            backend_url = f"{BACKEND_URL}{self.path}"
            
            print(f"Proxying {self.command} {self.path} to {backend_url}")
            
            # Create request to backend
            req = urllib.request.Request(backend_url, data=post_data, method=self.command)
            
            # Copy relevant headers
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)
            
            # Make request to backend
            with urllib.request.urlopen(req) as response:
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
                
                print(f"✅ Successfully proxied to backend: {response.status}")
                
        except HTTPError as e:
            print(f"❌ Backend error: {e.code} - {e.reason}")
            self.send_response(e.code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            print(f"❌ Proxy error: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"error": f"Proxy error: {str(e)}"}).encode()
            self.wfile.write(error_response)
 
if __name__ == "__main__":
    with socketserver.TCPServer(("", FRONTEND_PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"🌐 Proxy server running at http://localhost:{FRONTEND_PORT}")
        print(f"📁 Serving frontend files from {DIST_DIR}/")
        print(f"🔄 Proxying API calls to {BACKEND_URL}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Proxy server stopped")
