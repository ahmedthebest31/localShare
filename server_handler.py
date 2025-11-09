# server_handler.py
import http.server
import socketserver
import threading
import socket
import base64 
# (NO MORE CGI IMPORT - This fixes ModuleNotFoundError)
from PySide6.QtCore import Signal, QObject

# (WorkerSignals class is unchanged)
class WorkerSignals(QObject):
    server_started = Signal(str, int) 
    log_message = Signal(str)
    server_stopped = Signal()

# This class runs the HTTP server in a separate thread
class ServerThread(threading.Thread):
    def __init__(self, port, share_path, password=None):
        super().__init__()
        self.port = port
        self.share_path = share_path
        self.password = password 
        self.signals = WorkerSignals()
        self.httpd = None

    def run(self):
        try:
            # This is the handler that will serve files
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                
                SERVER_PASSWORD = self.password

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                
                def do_AUTHHEAD(self):
                    """Sends the 'WWW-Authenticate' header"""
                    self.send_response(401)
                    self.send_header('WWW-Authenticate', 'Basic realm=\"localShare Login\"')
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'401 Unauthorized: Access Denied')

                # --- MODIFIED: do_GET (Handles anonymous username) ---
                def do_GET(self):
                    """Handle GET requests with password check"""
                    
                    # 1. Check for password
                    if self.SERVER_PASSWORD:
                        auth_header = self.headers.get('Authorization')
                        if auth_header is None:
                            self.do_AUTHHEAD()
                            server_thread.signals.log_message.emit(f"[Auth] No auth header from {self.address_string()}. Sent 401.")
                            return
                        
                        try:
                            auth_type, auth_token = auth_header.split(' ', 1)
                            if auth_type.lower() != 'basic':
                                self.do_AUTHHEAD()
                                server_thread.signals.log_message.emit(f"[Auth] Invalid auth type from {self.address_string()}.")
                                return

                            decoded_credentials = base64.b64decode(auth_token).decode('utf-8')
                            username, password = decoded_credentials.split(':', 1)
                            
                            if password == self.SERVER_PASSWORD:
                                self.username = username # Store username
                                server_thread.signals.log_message.emit(f"[Auth] Login successful for user '{username}' from {self.address_string()}")
                            else:
                                self.do_AUTHHEAD()
                                server_thread.signals.log_message.emit(f"[Auth] Failed login (wrong pass) from user '{username}' @ {self.address_string()}.")
                                return
                        except Exception as e:
                            self.do_AUTHHEAD()
                            server_thread.signals.log_message.emit(f"[Auth] Error decoding auth: {e}")
                            return
                    
                    # 2. --- THIS IS THE FIX (for Problem 2) ---
                    # If no password, get username from IP/Hostname
                    else:
                        try:
                            # Try to get the hostname (e.g., "Ahmeds-PC")
                            self.username = socket.gethostbyaddr(self.client_address[0])[0]
                        except Exception:
                            # Fallback to the IP if lookup fails
                            self.username = self.client_address[0] 
                    
                    # 3. Proceed as normal
                    return super().do_GET()

                def log_message(self, format, *args):
                    # Check if username was set (it should always be set now)
                    user = getattr(self, 'username', 'unknown') 
                    server_thread.signals.log_message.emit(f"[Access] ({user}) {self.address_string()} - {format % args}")

            # (Factory and Server type are unchanged from last fix)
            def handler_factory(*args, **kwargs):
                return CustomHandler(*args, directory=self.share_path, **kwargs)

            server_thread = self 
            
            # Using HTTPServer (single-threaded) fixes the shutdown deadlock
            self.httpd = http.server.HTTPServer(("", self.port), handler_factory)
            
            ip = self.get_local_ip()
            self.signals.server_started.emit(ip, self.port)
            self.httpd.serve_forever() 

        except Exception as e:
            self.signals.log_message.emit(f"[Error] {e}")
        finally:
            self.signals.server_stopped.emit()

    def stop(self):
        # (Unchanged)
        if self.httpd:
            self.signals.log_message.emit("log_server_stopping") 
            self.httpd.shutdown() 
            self.httpd.server_close()

    def get_local_ip(self):
        # (Unchanged)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80)) 
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"