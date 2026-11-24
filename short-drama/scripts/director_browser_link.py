"""Transfer an official Studio launch URL to the chosen local browser once."""
import hmac
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit


def offer(launch, ttl=120):
    target = urlsplit(launch)
    if (target.scheme, target.hostname, target.path) != ('http', '127.0.0.1', '/open'):
        raise ValueError('Expected a local Studio launch URL')
    ticket = '/open/' + secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if (self.headers.get('Host') != authority or
                    not hmac.compare_digest(self.path, ticket) or
                    self.headers.get('Sec-Fetch-Mode', 'navigate') != 'navigate' or
                    self.headers.get('Sec-Purpose') == 'prefetch' or
                    self.headers.get('Purpose') == 'prefetch'):
                self.send_error(404)
                return
            self.send_response(302)
            self.send_header('Location', launch)
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            self.server.used = True

    with HTTPServer(('127.0.0.1', 0), Handler) as server:
        authority = '127.0.0.1:' + str(server.server_port)
        server.used = False
        print(json.dumps({'browserLink': 'http://' + authority + ticket,
                          'expiresInSeconds': ttl}), flush=True)
        deadline = time.monotonic() + ttl
        while not server.used and time.monotonic() < deadline:
            server.timeout = max(0.01, deadline - time.monotonic())
            server.handle_request()
        return 0 if server.used else 1
