
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('health_check')

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the health check server"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.end_headers()
            self.wfile.write(b"OK - Health check passed")
            logger.info("Health check request successful")
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not found")
            logger.info(f"Request to unknown path: {self.path}")

    def log_message(self, format, *args):
        """Override to avoid duplicate logging"""
        return

def start_health_check_server(port=7860):
    """Start a simple HTTP server to handle health checks"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, HealthCheckHandler)
        logger.info(f"Starting health check server on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health check server: {e}")

if __name__ == "__main__":
    start_health_check_server()
