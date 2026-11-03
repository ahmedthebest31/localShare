# server_handler.py
import os
import socket
import mimetypes
from flask import Flask, render_template_string, request, send_from_directory, Response, abort
from werkzeug.utils import secure_filename
from PySide6.QtCore import QObject, Signal
import threading

# The browser page template lives in web_template.py (HTML_TEMPLATE).
from web_template import HTML_TEMPLATE

class WorkerSignals(QObject):
    server_started = Signal(str, int)
    log_message = Signal(str)
    server_stopped = Signal()

def unique_filename(directory, filename):
    """Return a filename inside directory that does not collide with an existing file."""
    base, ext = os.path.splitext(filename)
    candidate = filename
    counter = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base} ({counter}){ext}"
        counter += 1
    return candidate

class ServerThread(threading.Thread):
    def __init__(self, port, share_path, password=None, allow_upload=False, rename_upload=False, max_upload_size=0):
        super().__init__()
        self.port = port
        self.share_path = os.path.abspath(share_path)
        self.password = password
        self.allow_upload = allow_upload
        self.rename_upload = rename_upload
        self.max_upload_size = max_upload_size
        self.signals = WorkerSignals()
        self.flask_app = self._create_flask_app()
        self.server = None

    def _create_flask_app(self):
        app = Flask(__name__)
        app.config['SHARE_PATH'] = self.share_path
        app.config['PASSWORD'] = self.password
        app.config['ALLOW_UPLOAD'] = self.allow_upload
        app.config['RENAME_UPLOAD'] = self.rename_upload
        if self.max_upload_size > 0:
            app.config['MAX_CONTENT_LENGTH'] = self.max_upload_size * 1024 * 1024

        def get_username_or_auth_response():
            if app.config['PASSWORD']:
                auth = request.authorization
                if not auth or not auth.username or auth.password != app.config['PASSWORD']:
                    return Response(
                        'Login Required', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})
                return auth.username
            else:
                try:
                    return socket.gethostbyaddr(request.remote_addr)[0]
                except Exception:
                    return request.remote_addr

        def get_file_icon(filename):
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

        @app.route('/', methods=['GET', 'POST'])
        def index():
            user = get_username_or_auth_response()
            if isinstance(user, Response):
                self.signals.log_message.emit(f"[Auth] Failed login attempt from {request.remote_addr}.")
                return user
            
            if request.method == 'GET':
                 self.signals.log_message.emit(f"[Access] ({user}) {request.remote_addr} - GET /")

            if request.method == 'POST':
                if not app.config['ALLOW_UPLOAD']:
                    self.signals.log_message.emit(f"[Upload] Rejected upload from {user} (disabled).")
                    abort(403)
                
                file = request.files.get('filetoupload')
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if not filename:
                        self.signals.log_message.emit(f"[Upload] Rejected upload from {user}: invalid filename.")
                        abort(400)
                    if app.config['RENAME_UPLOAD'] and user != request.remote_addr:
                        name, ext = os.path.splitext(filename)
                        final_filename = f"{name} (from {user}){ext}"
                    else:
                        final_filename = filename

                    saved_name = unique_filename(app.config['SHARE_PATH'], final_filename)
                    share_path_real = os.path.realpath(app.config['SHARE_PATH'])
                    upload_path_real = os.path.realpath(os.path.join(share_path_real, saved_name))
                    if upload_path_real == share_path_real or not upload_path_real.startswith(share_path_real + os.sep):
                        self.signals.log_message.emit(f"[Security] Blocked potential directory traversal upload from {user} for filename '{saved_name}'")
                        abort(403)

                    file.save(upload_path_real)
                    self.signals.log_message.emit(f"[Upload] Success: '{saved_name}' from {user}")

            file_info_list = []
            try:
                for f in sorted(os.listdir(app.config['SHARE_PATH'])):
                    if os.path.isfile(os.path.join(app.config['SHARE_PATH'], f)):
                        file_info_list.append({"name": f, "icon": get_file_icon(f)})
            except Exception as e:
                self.signals.log_message.emit(f"[Error] Could not list files: {e}")

            html = render_template_string(HTML_TEMPLATE,
                title="localShare",
                allow_upload=app.config['ALLOW_UPLOAD'],
                files=file_info_list
            )
            response = Response(html, mimetype="text/html")
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Pragma'] = 'no-cache'
            return response

        @app.route('/files/<path:filename>')
        def download_file(filename):
            user = get_username_or_auth_response()
            if isinstance(user, Response):
                return user
            
            share_path_real = os.path.realpath(app.config['SHARE_PATH'])
            requested_path_real = os.path.realpath(os.path.join(share_path_real, filename))

            if requested_path_real == share_path_real or not requested_path_real.startswith(share_path_real + os.sep):
                self.signals.log_message.emit(f"[Security] Path traversal attempt blocked from {request.remote_addr} for '{filename}'")
                abort(404)

            if not os.path.isfile(requested_path_real):
                abort(404)

            self.signals.log_message.emit(f"[Access] ({user}) {request.remote_addr} - GET /files/{filename}")
            response = send_from_directory(app.config['SHARE_PATH'], filename, as_attachment=False)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response

        @app.errorhandler(413)
        def file_too_large(e):
            self.signals.log_message.emit("[Upload] Rejected upload: file exceeds the configured size limit.")
            return "File too large.", 413

        return app

    def run(self):
        try:
            from werkzeug.serving import make_server
            
            class Server(threading.Thread):
                def __init__(self, app, host, port):
                    super().__init__()
                    self.srv = make_server(host, port, app, threaded=True)
                    self.ctx = app.app_context()
                    self.ctx.push()

                def run(self):
                    self.srv.serve_forever()

                def shutdown(self):
                    self.srv.shutdown()

            ip = self.get_local_ip()
            self.server = Server(self.flask_app, '0.0.0.0', self.port)
            self.signals.server_started.emit(ip, self.port)
            self.server.start()
            self.server.join()

        except OSError as e:
            if "address already in use" in str(e).lower():
                self.signals.log_message.emit(f"[Error] Port {self.port} is already in use.")
            else:
                self.signals.log_message.emit(f"[Error] {e}")
        except Exception as e:
            self.signals.log_message.emit(f"[Error] {e}")
        finally:
            self.signals.server_stopped.emit()

    def stop(self):
        if self.server is not None and self.server.is_alive():
            self.signals.log_message.emit("log_server_stopping")
            self.server.shutdown()

    def get_local_ip(self):
        """Best-effort local IPv4 address using multiple strategies."""
        candidates = set()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                candidates.add(s.getsockname()[0])
        except Exception:
            pass
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                candidates.add(info[4][0])
        except Exception:
            pass
        for ip in sorted(candidates):
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                return ip
        return "127.0.0.1"