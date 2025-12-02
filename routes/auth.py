# routes/auth.py
from flask import Blueprint, request, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from db import get_db

import time
from collections import defaultdict

bp_auth = Blueprint("auth", __name__)
ph = PasswordHasher()

# ---- Simple time-window rate limiter (10 requests/sec per IP) ----
RATE_LIMIT = 10          # requests
WINDOW_SECONDS = 1.0     # per this many seconds

# Store per-IP counters in memory: { ip: {"window_start": float, "count": int} }
request_counters = defaultdict(lambda: {"window_start": 0.0, "count": 0})


def is_rate_limited(ip: str) -> bool:
    """
    Return True if this IP has exceeded RATE_LIMIT within WINDOW_SECONDS.
    """
    now = time.time()
    entry = request_counters[ip]

    # If current window has expired, reset it
    if now - entry["window_start"] > WINDOW_SECONDS:
        entry["window_start"] = now
        entry["count"] = 0

    # Count this request
    entry["count"] += 1

    # If over the limit, it's rate-limited
    return entry["count"] > RATE_LIMIT


@bp_auth.post("/auth")
def auth():
    """
    POST /auth
    Body JSON: {"username": "...", "password": "..."}

    - Rate limit: at most 10 requests/sec per IP.
    - Look up user by username.
    - Verify password using Argon2.
    - If valid: log auth request in auth_logs with IP + user_id.
    - Return 200 on success, 401 on failure, 429 if rate-limited.
    """
    client_ip = request.remote_addr or "unknown"

    # 1) Rate limit check FIRST
    if is_rate_limited(client_ip):
        return jsonify({"error": "too many requests"}), 429

    # 2) Normal auth logic
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    conn = get_db()
    cur = conn.cursor()

    user = cur.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "invalid credentials"}), 401

    try:
        ph.verify(user["password_hash"], password)
    except VerifyMismatchError:
        conn.close()
        return jsonify({"error": "invalid credentials"}), 401

    # 3) If password OK → log this auth request
    cur.execute(
        "INSERT INTO auth_logs (request_ip, user_id) VALUES (?, ?)",
        (client_ip, user["id"])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "authenticated"}), 200
