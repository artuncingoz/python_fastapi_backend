# tests/test_auth_notes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _signup(email="t@e.com", password="Passw0rd!"):
    return client.post("/api/v1/auth/signup", json={"email": email, "password": password})

def _login(email="t@e.com", password="Passw0rd!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})

def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_signup_login_create_note_flow():
    # signup
    r = _signup()
    assert r.status_code == 201, r.text

    # login
    r = _login()
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = _auth_headers(token)

    # Info about me
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "t@e.com"

    # create note (enqueues job into fakeredis; no real worker)
    r = client.post("/api/v1/notes", json={"raw_text": "hello world " * 50}, headers=headers)
    assert r.status_code == 200, r.text
    note = r.json()
    assert note["status"] in ("queued", "processing", "done", "failed")
    note_id = note["id"]

    # list my notes (should include the one we just created)
    r = client.get("/api/v1/notes?limit=10&offset=0", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert any(n["id"] == note_id for n in items)

    # get-by-id
    r = client.get(f"/api/v1/notes/{note_id}", headers=headers)
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == note_id

def test_admin_only_routes_guarded():
    # agent
    _signup(email="user1@example.com")
    r = _login(email="user1@example.com")
    token_user = r.json()["access_token"]
    headers_user = _auth_headers(token_user)

    # should be 403 on admin-only list-all
    r = client.get("/api/v1/notes/all", headers=headers_user)
    assert r.status_code in (401, 403)

