import http.server
import socketserver
import urllib.parse
import subprocess
import base64

PORT = 25000

AUTH_KEY_BASE64 = "MDAwMGN5YmVyc2VjX2dyb3VwX3J0XzAwMDAwMAo="

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        auth_header = self.headers.get('Authorization')

        if auth_header is None or not auth_header.startswith('Basic'):
            self.send_response(401)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Authorization header is missing or incorrect")
            return

        # Extraer la clave enviada por el cliente (en Base64)
        encoded_key = auth_header.split('Basic ')[1]

        # Decodificar la clave almacenada en Base64
        decoded_stored_key = base64.b64decode(AUTH_KEY_BASE64).decode().strip()  # Eliminar saltos de línea

        # Decodificar la clave enviada por el cliente
        decoded_client_key = base64.b64decode(encoded_key).decode().strip()  # Eliminar saltos de línea

        # Comparar las claves
        if decoded_client_key != decoded_stored_key:
            self.send_response(403)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid authorization key")
            return

        # Procesar el parámetro 'exec'
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if 'exec' in query_params:
            command = query_params['exec'][0]
            try:
                allowed_commands = ['ls', 'whoami']
                if not any(command.startswith(cmd) for cmd in allowed_commands):
                    self.send_response(403)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Command not allowed.")
                    return

                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(result)
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(e.output)
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing 'exec' parameter in URL")

with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()
