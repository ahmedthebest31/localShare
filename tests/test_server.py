# tests/test_server.py
import io
import os
import tempfile
import pytest

from server_handler import ServerThread, unique_filename


@pytest.fixture
def tmp_share():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def app(tmp_share):
    thread = ServerThread(8000, tmp_share)
    return thread._create_flask_app(), tmp_share


def test_unique_filename_no_collision(tmp_share):
    result = unique_filename(tmp_share, "report.pdf")
    assert result == "report.pdf"


def test_unique_filename_collision(tmp_share):
    existing = os.path.join(tmp_share, "report.pdf")
    with open(existing, "w", encoding="utf-8") as f:
        f.write("x")
    result = unique_filename(tmp_share, "report.pdf")
    assert result == "report (1).pdf"


def test_index_lists_files(app):
    flask_app, share = app
    with open(os.path.join(share, "hello.txt"), "w", encoding="utf-8") as f:
        f.write("hi")
    client = flask_app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"hello.txt" in resp.data


def test_download_file(app):
    flask_app, share = app
    with open(os.path.join(share, "data.bin"), "wb") as f:
        f.write(b"\x00\x01\x02")
    client = flask_app.test_client()
    resp = client.get("/files/data.bin")
    assert resp.status_code == 200
    assert resp.data == b"\x00\x01\x02"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


def test_auth_required_returns_401(tmp_share):
    thread = ServerThread(8000, tmp_share, password="secret")
    flask_app = thread._create_flask_app()
    client = flask_app.test_client()
    resp = client.get("/")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate", "").startswith("Basic")


def test_auth_accepts_correct_password(tmp_share):
    thread = ServerThread(8000, tmp_share, password="secret")
    flask_app = thread._create_flask_app()
    client = flask_app.test_client()
    resp = client.get("/", headers={"Authorization": "Basic c2VjcmV0OnNlY3JldA=="})
    assert resp.status_code == 200


def test_traversal_blocked(app):
    flask_app, share = app
    with open(os.path.join(share, "real.txt"), "w", encoding="utf-8") as f:
        f.write("ok")
    client = flask_app.test_client()
    resp = client.get("/files/../pyproject.toml")
    assert resp.status_code == 404


def test_upload_disabled_returns_403(app):
    flask_app, share = app
    client = flask_app.test_client()
    data = {"filetoupload": (os.urandom(4), "evil.txt")}
    resp = client.post("/", data=data, content_type="multipart/form-data")
    assert resp.status_code == 403
    assert not os.path.exists(os.path.join(share, "evil.txt"))


def test_upload_enabled_saves_file(tmp_share):
    thread = ServerThread(8000, tmp_share, allow_upload=True)
    flask_app = thread._create_flask_app()
    client = flask_app.test_client()
    data = {"filetoupload": (io.BytesIO(b"hello upload"), "up.txt")}
    resp = client.post("/", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    saved = os.path.join(tmp_share, "up.txt")
    assert os.path.exists(saved)
    with open(saved, "r", encoding="utf-8") as f:
        assert f.read() == "hello upload"


def test_upload_overwrite_protected(tmp_share):
    thread = ServerThread(8000, tmp_share, allow_upload=True)
    flask_app = thread._create_flask_app()
    client = flask_app.test_client()
    with open(os.path.join(tmp_share, "same.txt"), "w", encoding="utf-8") as f:
        f.write("original")
    data = {"filetoupload": (io.BytesIO(b"replacement"), "same.txt")}
    resp = client.post("/", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert os.path.exists(os.path.join(tmp_share, "same (1).txt"))
    with open(os.path.join(tmp_share, "same.txt"), "r", encoding="utf-8") as f:
        assert f.read() == "original"


def test_upload_size_limit_returns_413(tmp_share):
    thread = ServerThread(8000, tmp_share, allow_upload=True, max_upload_size=1)
    flask_app = thread._create_flask_app()
    client = flask_app.test_client()
    data = {"filetoupload": (io.BytesIO(b"x" * (2 * 1024 * 1024)), "big.bin")}
    resp = client.post("/", data=data, content_type="multipart/form-data")
    assert resp.status_code == 413


def test_stop_without_running_server_does_not_crash(tmp_share):
    thread = ServerThread(8000, tmp_share)
    thread.stop()


def test_stop_after_failed_bind_does_not_crash(tmp_share, monkeypatch):
    def fake_make_server(*args, **kwargs):
        raise OSError("[WinError 10048] address already in use")

    monkeypatch.setattr("werkzeug.serving.make_server", fake_make_server)
    thread = ServerThread(8000, tmp_share)
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive()
    thread.stop()
