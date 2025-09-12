# tests/test_auth_notes.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_signup_login_create_note_flow():
    # signup
    r = client.post("/api/v1/auth/signup", json={"email": "t@e.com", "password": "Passw0rd!"})
    assert r.status_code == 201, r.text

    # login
    r = client.post("/api/v1/auth/login", json={"email": "t@e.com", "password": "Passw0rd!"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create note (this enqueues an RQ job into fakeredis; no worker runs in unit tests)
    r = client.post("/api/v1/notes", json={"raw_text": "hello world " * 80}, headers=headers)
    assert r.status_code == 200, r.text
    note_id = r.json()["id"]

    # poll once — without a worker, status will likely be 'queued' (which we accept)
    r = client.get(f"/api/v1/notes/{note_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] in ("queued", "processing", "done", "failed")
