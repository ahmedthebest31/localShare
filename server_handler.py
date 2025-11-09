# server_handler.py
import http.server
import socketserver
import threading
import socket
from PySide6.QtCore import Signal, QObject

# This class will emit signals from the server thread to the main UI thread
class WorkerSignals(QObject):
    server_started = Signal(str, int) # (ip, port)
    log_message = Signal(str)
    server_stopped = Signal()

# This class runs the HTTP server in a separate thread
class ServerThread(threading.Thread):
    def __init__(self, port, share_path):
        super().__init__()
        self.port = port
        self.share_path = share_path
        self.signals = WorkerSignals()
        self.httpd = None

    def run(self):
        try:
            # --- THIS IS THE FIX ---
            # We use functools.partial to 'inject' the directory
            # argument into the Handler *before* the server creates it.
            # (We will import functools in main.py, but we're defining the handler here)
            
            # This is the handler that will serve files
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    # We pass the 'directory' kwarg to the super constructor
                    super().__init__(*args, **kwargs)
                
                # Log requests to our UI
                def log_message(self, format, *args):
                    # We must find the signals object this way
                    server_thread.signals.log_message.emit(f"[Access] {self.address_string()} - {format % args}")

            # This is how we pass the share_path to the handler
            # We must use a factory function or partial
            def handler_factory(*args, **kwargs):
                return CustomHandler(*args, directory=self.share_path, **kwargs)

            # Keep a reference to this thread to access signals
            server_thread = self # Allow handler to access self.signals

            self.httpd = socketserver.TCPServer(("", self.port), handler_factory)
            
            # Find local IP
            ip = self.get_local_ip()
            
            # Emit signal that server has started
            self.signals.server_started.emit(ip, self.port)
            
            self.httpd.serve_forever()

        except Exception as e:
            self.signals.log_message.emit(f"[Error] {e}")
        finally:
            self.signals.server_stopped.emit()

    def stop(self):
        if self.httpd:
            self.signals.log_message.emit("Stopping server...") # (We will translate this in main.py)
            self.httpd.shutdown()
            self.httpd.server_close()

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80)) # Connect to a public server
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1" # Fallback