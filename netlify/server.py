#!/usr/bin/env python3
"""Simple HTTP server for local development"""
import http.server
import socketserver
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request
import urllib.error

PORT = 8004
os.chdir(Path(__file__).parent)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching during development
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        if self.path.startswith('/proxy'):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        if self.path.startswith('/proxy'):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/proxy':
            query = parse_qs(parsed.query)
            target = query.get('url', [''])[0]
            if not target:
                return self.send_error(400, 'Missing target url')
            return self._proxy_request(target, method='GET')
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/proxy':
            query = parse_qs(parsed.query)
            target = query.get('url', [''])[0]
            if not target:
                return self.send_error(400, 'Missing target url')
            return self._proxy_request(target, method='POST')
        return super().do_POST()

    def _proxy_request(self, target, method='GET'):
        target = unquote(target)
        parsed = urlparse(target)
        if parsed.scheme not in ('http', 'https') or parsed.netloc != 'script.google.com':
            return self.send_error(403, 'Forbidden target')

        content_length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(content_length) if content_length else None
        req = urllib.request.Request(target, data=body, method=method)
        if self.headers.get('Content-Type'):
            req.add_header('Content-Type', self.headers['Content-Type'])
        req.add_header('User-Agent', 'LocalProxy/1.0')
        req.add_header('Accept-Encoding', 'identity')
        req.add_header('Connection', 'close')

        try:
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                content = response.read()
                enc = (response.getheader('Content-Encoding') or '').lower()
                if 'gzip' in enc or content[:2] == b'\x1f\x8b':
                    import gzip
                    try:
                        content = gzip.decompress(content)
                    except Exception:
                        pass
                elif 'deflate' in enc or 'zlib' in enc:
                    import zlib
                    try:
                        content = zlib.decompress(content)
                    except Exception:
                        pass
                for header, value in response.getheaders():
                    if header.lower() in ('transfer-encoding', 'content-length', 'connection', 'content-encoding'):
                        continue
                    self.send_header(header, value)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except urllib.error.HTTPError as err:
            self.send_response(err.code)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(err.read())))
            self.end_headers()
            self.wfile.write(err.read())
        except Exception as err:
            self.send_error(502, f'Proxy error: {err}')

    def log_message(self, format, *args):
        # Custom logging
        print(f"[SERVER] {self.address_string()} - {format % args}")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"\n✅ Server running at http://localhost:{PORT}")
    print(f"📂 Serving files from: {os.getcwd()}")
    print(f"🌐 Open your app: http://localhost:{PORT}/index.html")
    print(f"\n⏹️  Press Ctrl+C to stop the server\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
