# routes/register.py
from flask import Blueprint, request, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from uuid import uuid4

from db import get_db

bp_register = Blueprint("register", __name__)
ph = PasswordHasher()


@bp_register.post("/register")
def register():
    """
    POST /register
    Body JSON: {"username": "...", "email": "..."}
    - Generate UUIDv4 password
    - Hash with Argon2
    - Store in users table
    - Return {"password": "..."} with 201
    """
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    email = data.get("email")

    if not username:
        return jsonify({"error": "username is required"}), 400

    # 1) generate a secure password (UUIDv4)
    generated_password = str(uuid4())

    # 2) hash the password with Argon2
    password_hash = ph.hash(generated_password)

    # 3) store into users table
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "could not create user"}), 400
    finally:
        conn.close()

    # 4) return the plain generated password to the user
    return jsonify({"password": generated_password}), 201
