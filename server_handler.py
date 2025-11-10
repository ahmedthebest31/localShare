# server_handler.py
import http.server
import socketserver
import threading
import socket
import base64 
import os 
import shutil 
import functools
from email.parser import BytesParser 
from PySide6.QtCore import Signal, QObject
import mimetypes 
from urllib.parse import unquote 

# (HTML_TEMPLATE and WorkerSignals are unchanged)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --text-color: #212529;
            --container-bg: #ffffff;
            --border-color: #dee2e6;
            --primary-color: #007bff;
            --primary-hover: #0056b3;
            --shadow: 0 0.125rem 0.25rem rgba(0,0,0,.075);
        }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
            margin: 0; 
            padding: 1.5em; 
            background: var(--bg-color); 
            color: var(--text-color);
        }}
        .container {{ 
            max-width: 900px; 
            margin: 0 auto; 
            background: var(--container-bg); 
            border: 1px solid var(--border-color);
            border-radius: 8px; 
            padding: 1.5em 2em;
            box-shadow: var(--shadow);
        }}
        h1, h2 {{ border-bottom: 2px solid var(--border-color); padding-bottom: 10px; }}
        
        /* Upload Form */
        form {{ margin-bottom: 1.5em; }}
        input[type=file] {{ 
            border: 1px solid var(--border-color); 
            padding: 10px; 
            border-radius: 4px; 
            width: 100%;
            box-sizing: border-box;
        }}
        input[type=submit] {{ 
            background: var(--primary-color); color: white; border: none; 
            padding: 12px 18px; border-radius: 4px; cursor: pointer; 
            font-size: 16px; font-weight: 500; margin-top: 10px;
        }}
        input[type=submit]:hover {{ background: var(--primary-hover); }}

        /* File List Header */
        .file-header {{ display: flex; justify-content: space-between; align-items: center; }}
        #toggleView {{ 
            background: #6c757d; color: white; border: none;
            padding: 8px 12px; border-radius: 4px; cursor: pointer;
        }}
        #toggleView:hover {{ background: #5a6268; }}

        /* File List */
        #file-list ul {{ list-style: none; padding: 0; margin-top: 1em; }}
        
        /* List View (Default) */
        #file-list.list-view li a {{
            display: flex; align-items: center;
            padding: 12px 15px; margin-bottom: 5px; 
            border: 1px solid var(--border-color); border-radius: 4px;
            text-decoration: none; color: var(--primary-color);
            background: #fff; transition: background 0.2s;
        }}
        #file-list.list-view li a:hover {{ background: #f1f3f5; }}
        
        /* Grid View */
        #file-list.grid-view ul {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            grid-gap: 15px;
        }}
        #file-list.grid-view li a {{
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 120px;
            padding: 10px; border: 1px solid var(--border-color); border-radius: 4px;
            text-decoration: none; color: #333;
            background: #fff; text-align: center;
            word-break: break-all;
        }}
        #file-list.grid-view li a:hover {{ box-shadow: var(--shadow); }}
        
        /* File Icons (Simple) */
        .icon::before {{ 
            font-size: 24px; margin-right: 10px; 
            font-family: 'Arial', sans-serif;
        }}
        #file-list.grid-view .icon::before {{ font-size: 40px; margin-right: 0; margin-bottom: 10px; }}
        
        .icon-file::before {{ content: '📄'; }} /* Default */
        .icon-video::before {{ content: '🎬'; }}
        .icon-audio::before {{ content: '🎵'; }}
        .icon-image::before {{ content: '🖼️'; }}
        .icon-archive::before {{ content: '📦'; }}
        .icon-text::before {{ content: '📝'; }}

    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        {upload_form_html}
        
        <div class="file-header">
            <h2>Shared Files</h2>
            <button id="toggleView" title="Toggle View">Toggle View</button>
        </div>
        <div id="file-list" class="list-view">
            <ul>
                {file_list_html}
            </ul>
        </div>
    </div>
    
    <script>
        document.getElementById('toggleView').addEventListener('click', function() {{
            var list = document.getElementById('file-list');
            // Toggle class and save preference
            if (list.classList.toggle('grid-view', list.classList.contains('list-view'))) {{
                list.classList.remove('list-view');
                localStorage.setItem('viewMode', 'grid');
            }} else {{
                list.classList.add('list-view');
                localStorage.setItem('viewMode', 'list');
            }}
        }});
        // Restore preference on load
        (function() {{
            var view = localStorage.getItem('viewMode');
            if (view === 'grid') {{
                var list = document.getElementById('file-list');
                list.classList.remove('list-view');
                list.classList.add('grid-view');
            }}
        }})();
    </script>
</body>
</html>
"""

class WorkerSignals(QObject):
    server_started = Signal(str, int) 
    log_message = Signal(str)
    server_stopped = Signal()

class ServerThread(threading.Thread):
    def __init__(self, port, share_path, password=None, allow_upload=False, rename_upload=False):
        super().__init__()
        self.port = port
        self.share_path = share_path
        self.password = password 
        self.allow_upload = allow_upload 
        self.rename_upload = rename_upload 
        self.signals = WorkerSignals()
        self.httpd = None

    def run(self):
        try:
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                
                # --- *** THE FIX IS HERE *** ---
                # We can't access ServerThread's 'self' from the class body.
                # So we must pass the variables in __init__
                
                def __init__(self, *args, 
                             directory=None, 
                             password=None, 
                             allow_upload=False, 
                             rename_upload=False, 
                             **kwargs):
                    
                    # Store the settings on the HANDLER'S 'self'
                    self.SERVER_PASSWORD = password
                    self.ALLOW_UPLOAD = allow_upload
                    self.RENAME_UPLOAD = rename_upload
                    
                    if directory is None:
                        directory = os.getcwd()
                    
                    # This is the critical line that fixes the crash.
                    # We MUST pass the directory to the parent class __init__.
                    super().__init__(*args, directory=directory, **kwargs)
                
                def do_AUTHHEAD(self):
                    """Sends the 'WWW-Authenticate' header"""
                    self.send_response(401)
                    self.send_header('WWW-Authenticate', 'Basic realm=\"localShare Login\"')
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'401 Unauthorized: Access Denied')

                def get_username(self):
                    """Gets username from auth or IP/Hostname. Returns True if login is ok."""
                    self.username = "anonymous" # Default
                    
                    if self.SERVER_PASSWORD:
                        auth_header = self.headers.get('Authorization')
                        if auth_header is None:
                            self.do_AUTHHEAD()
                            server_thread.signals.log_message.emit(f"[Auth] No auth header from {self.address_string()}. Sent 401.")
                            return False
                        
                        try:
                            auth_type, auth_token = auth_header.split(' ', 1)
                            if auth_type.lower() != 'basic':
                                self.do_AUTHHEAD()
                                server_thread.signals.log_message.emit(f"[Auth] Invalid auth type from {self.address_string()}.")
                                return False

                            decoded_credentials = base64.b64decode(auth_token).decode('utf-8')
                            username, password = decoded_credentials.split(':', 1)
                            
                            if password == self.SERVER_PASSWORD:
                                self.username = username 
                                if self.command == 'GET':
                                    server_thread.signals.log_message.emit(f"[Auth] Login successful for user '{username}' from {self.address_string()}")
                                return True
                            else:
                                self.do_AUTHHEAD()
                                server_thread.signals.log_message.emit(f"[Auth] Failed login (wrong pass) from user '{username}' @ {self.address_string()}.")
                                return False
                        except Exception as e:
                            self.do_AUTHHEAD()
                            server_thread.signals.log_message.emit(f"[Auth] Error decoding auth: {e}")
                            return False
                    
                    else:
                        try:
                            self.username = socket.gethostbyaddr(self.client_address[0])[0]
                        except Exception:
                            self.username = self.client_address[0] 
                        return True
                
                def do_GET(self):
                    """Handle GET requests: check password, then send custom HTML or file."""
                    if not self.get_username():
                        return
                    
                    if self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        html_content = self.generate_html_page()
                        self.wfile.write(html_content.encode('utf-8'))
                        return
                    
                    # The parent class now works because __init__ was fixed
                    return super().do_GET()

                def do_POST(self):
                    """Handle POST requests for file uploads."""
                    
                    if not self.get_username():
                        return 

                    if not self.ALLOW_UPLOAD:
                        self.send_error(403, "Forbidden: Uploads are disabled.")
                        server_thread.signals.log_message.emit(f"[Upload] Rejected upload from {self.username} (disabled).")
                        return

                    try:
                        headers = self.headers
                        content_length = int(headers['Content-Length'])
                        body = b"Content-Type: " + headers['Content-Type'].encode('utf-8') + \
                               b"\nContent-Length: " + str(content_length).encode('utf-8') + \
                               b"\n\n" + self.rfile.read(content_length)
                        
                        parser = BytesParser()
                        message = parser.parsebytes(body)

                        for part in message.get_payload():
                            if part.get_filename():
                                filename = part.get_filename()
                                file_data = part.get_payload(decode=True)
                                
                                if self.RENAME_UPLOAD and self.username != "anonymous":
                                    name, ext = os.path.splitext(filename)
                                    final_filename = f"{name} (from {self.username}){ext}"
                                else:
                                    final_filename = filename
                                
                                # Use self.directory (set in __init__)
                                save_path = os.path.join(self.directory, final_filename)
                                
                                with open(save_path, 'wb') as f:
                                    f.write(file_data)
                                
                                server_thread.signals.log_message.emit(f"[Upload] Success: '{final_filename}' ({len(file_data)} bytes) from {self.username}")

                    except Exception as e:
                        server_thread.signals.log_message.emit(f"[Upload] FAILED: {e}")
                        self.send_error(500, f"Internal Server Error: {e}")

                    self.send_response(303) 
                    self.send_header('Location', '/')
                    self.end_headers()

                def get_file_icon(self, filename):
                    """Helper to get a CSS class based on file type."""
                    mime_type, _ = mimetypes.guess_type(filename)
                    if not mime_type:
                        return "icon-file"
                    
                    main_type = mime_type.split('/')[0]
                    if main_type == "video":
                        return "icon-video"
                    if main_type == "audio":
                        return "icon-audio"
                    if main_type == "image":
                        return "icon-image"
                    if main_type == "text":
                        return "icon-text"
                    if "zip" in mime_type or "rar" in mime_type:
                        return "icon-archive"
                    return "icon-file"

                def generate_html_page(self):
                    """Generates the custom HTML page."""
                    
                    upload_form_html = ""
                    if self.ALLOW_UPLOAD:
                        upload_form_html = """
                        <div class="container">
                            <h2>Upload File</h2>
                            <form action="/" method="post" enctype="multipart/form-data">
                                <input type="file" name="filetoupload" required>
                                <input type="submit" value="Upload">
                            </form>
                        </div><br>
                        """
                    
                    file_list_html = ""
                    try:
                        # Use self.directory (set in __init__)
                        files = os.listdir(self.directory)
                        for f in sorted(files):
                            if os.path.isfile(os.path.join(self.directory, f)):
                                icon_class = self.get_file_icon(f)
                                # URL-encode filename to handle spaces, etc.
                                file_url = f"/{f.replace('?', '%3F').replace('#', '%23')}"
                                file_list_html += f"<li><a href='{file_url}'><span class='icon {icon_class}'></span>{f}</a></li>"
                    except Exception as e:
                        file_list_html = f"<li>Could not list files: {e}</li>"
                    
                    page = HTML_TEMPLATE.format(
                        title="localShare",
                        upload_form_html=upload_form_html,
                        file_list_html=file_list_html
                    )
                    return page
                
                def log_message(self, format, *args):
                    user = getattr(self, 'username', 'unknown') 
                    server_thread.signals.log_message.emit(f"[Access] ({user}) {self.address_string()} - {format % args}")

            # --- *** THE FIX IS HERE *** ---
            # We use functools.partial to 'bake in' ALL settings
            HandlerWithSettings = functools.partial(
                CustomHandler, 
                directory=self.share_path,
                password=self.password,
                allow_upload=self.allow_upload,
                rename_upload=self.rename_upload
            )

            server_thread = self 
            self.httpd = http.server.HTTPServer(("", self.port), HandlerWithSettings)
            
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