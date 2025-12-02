# tests/test_app.py
import json
import os
import sqlite3
import tempfile

import pytest
from dotenv import load_dotenv

# Load .env so NOT_MY_KEY is available
load_dotenv()

# IMPORTANT: import app AFTER loading env
import app as app_module  # this imports your app.py


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Use a temporary SQLite DB for tests so we don't pollute the real one.
    """
    # Point DB_NAME in db.py to a temp file
    test_db_path = tmp_path / "test_project3.db"
    monkeypatch.setattr(app_module, "app", app_module.app)

    # Monkeypatch DB_NAME used in db.py, if you used a global.
    import db as db_module
    db_module.DB_NAME = str(test_db_path)

    # Re-init DB and keys for this test DB
    db_module.init_db()
    from jwks import ensure_default_key
    ensure_default_key()

    app = app_module.app
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_ping(client):
    resp = client.get("/ping")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "project 3 jwks server alive"


def test_jwks_returns_keys(client):
    resp = client.get("/.well-known/jwks.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "keys" in data
    assert isinstance(data["keys"], list)
    assert len(data["keys"]) >= 1
    k = data["keys"][0]
    # basic JWK structure
    assert k["kty"] == "RSA"
    assert k["alg"] == "RS256"
    assert k["use"] == "sig"
    assert "kid" in k
    assert "n" in k
    assert "e" in k


def test_register_and_auth_and_logging(client, tmp_path):
    # Register a user
    resp = client.post(
        "/register",
        data=json.dumps({"username": "testuser", "email": "test@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code in (200, 201)
    data = resp.get_json()
    assert "password" in data
    password = data["password"]

    # Auth with that user
    resp2 = client.post(
        "/auth",
        data=json.dumps({"username": "testuser", "password": password}),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["message"] == "authenticated"

    # Check auth_logs has at least one row
    # Open the same test DB used above
    import db as db_module
    conn = sqlite3.connect(db_module.DB_NAME)
    cur = conn.cursor()
    rows = cur.execute("SELECT id, request_ip, user_id FROM auth_logs").fetchall()
    conn.close()

    assert len(rows) >= 1


def test_rate_limiter(client):
    """
    Spam /auth more than 10 times in one second; expect some 429 responses.
    """
    # First, register a user
    resp = client.post(
        "/register",
        data=json.dumps({"username": "rluser", "email": "rl@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code in (200, 201)
    pwd = resp.get_json()["password"]

    ok_count = 0
    too_many_count = 0

    for _ in range(15):
        resp2 = client.post(
            "/auth",
            data=json.dumps({"username": "rluser", "password": pwd}),
            content_type="application/json",
        )
        if resp2.status_code == 200:
            ok_count += 1
        elif resp2.status_code == 429:
            too_many_count += 1

    # We expect at least one 429 if rate limiting is working
    assert too_many_count >= 1
