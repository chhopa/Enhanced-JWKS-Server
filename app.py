# app.py
from flask import Flask, jsonify
from dotenv import load_dotenv

from db import init_db
from jwks import ensure_default_key, get_jwks
from routes.register import bp_register
from routes.auth import bp_auth

# Load .env (for NOT_MY_KEY)
load_dotenv()

app = Flask(__name__)

# Initialize database + ensure JWKS key exists
init_db()
ensure_default_key()

# Register route blueprints
app.register_blueprint(bp_register)
app.register_blueprint(bp_auth)


@app.get("/ping")
def ping():
    return jsonify({"message": "project 3 jwks server alive"}), 200


@app.get("/.well-known/jwks.json")
def jwks_route():
    return jsonify(get_jwks()), 200


if __name__ == "__main__":
    # Gradebot expects 8080 by default
    app.run(port=8080, debug=True)
