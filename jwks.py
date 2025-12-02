# jwks.py
import base64
import hashlib
import time

from Crypto.PublicKey import RSA

from db import get_db
from crypto import encrypt_private_key, decrypt_private_key


def _b64url_uint(val: int) -> str:
    """Convert an integer to base64url-encoded string without padding."""
    length = (val.bit_length() + 7) // 8
    as_bytes = val.to_bytes(length, byteorder="big")
    return base64.urlsafe_b64encode(as_bytes).rstrip(b"=").decode("ascii")


def _generate_rsa_key():
    """Generate RSA keypair and return (RSA object, private_pem string)."""
    key = RSA.generate(2048)
    private_pem = key.export_key().decode("utf-8")
    return key, private_pem


def _insert_new_key():
    """
    Generate RSA key, encrypt private key, insert into DB.
    Schema:
      kid INTEGER PRIMARY KEY AUTOINCREMENT,
      key BLOB NOT NULL,
      exp INTEGER NOT NULL
    """
    key, private_pem = _generate_rsa_key()

    encrypted_b64 = encrypt_private_key(private_pem)  # returns base64 text
    encrypted_bytes = encrypted_b64.encode("utf-8")

    exp_ts = int(time.time()) + 86400  # good for 1 day

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO keys (key, exp) VALUES (?, ?)",
        (encrypted_bytes, exp_ts),
    )
    conn.commit()
    conn.close()


def ensure_default_key():
    """Ensure at least one NON-EXPIRED key exists."""
    now = int(time.time())

    conn = get_db()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT COUNT(*) AS cnt FROM keys WHERE exp >= ?",
        (now,),
    ).fetchone()
    conn.close()

    if row["cnt"] == 0:
        _insert_new_key()


def _jwk_from_private(kid: int, private_pem: str) -> dict:
    """Convert private key → public JWK."""
    key = RSA.import_key(private_pem)
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": str(kid),
        "n": _b64url_uint(key.n),
        "e": _b64url_uint(key.e),
    }


def get_jwks() -> dict:
    """Return JWKS from encrypted DB keys."""
    now = int(time.time())
    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT kid, key FROM keys WHERE exp >= ?",
        (now,),
    ).fetchall()
    conn.close()

    jwk_list = []
    for r in rows:
        encrypted_b64 = r["key"].decode("utf-8")
        private_pem = decrypt_private_key(encrypted_b64)
        jwk_list.append(_jwk_from_private(r["kid"], private_pem))

    return {"keys": jwk_list}
