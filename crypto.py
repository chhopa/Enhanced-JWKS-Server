# crypto.py
import os
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

BLOCK_SIZE = 16  # AES block size in bytes


def _get_aes_key() -> bytes:
    """
    Derive a 32-byte AES key from the NOT_MY_KEY environment variable.
    The assignment says: use NOT_MY_KEY from env for AES encryption.
    """
    secret = os.getenv("NOT_MY_KEY")
    if not secret:
        raise RuntimeError(
            "NOT_MY_KEY environment variable is not set. "
            "Put NOT_MY_KEY=... in your .env file or export it in your shell."
        )

    # Use SHA-256 to get a 32-byte key from the string
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encrypt_private_key(plaintext: str) -> str:
    """
    Encrypt a private key (string) with AES-CBC.
    Returns base64(iv + ciphertext).
    """
    key = _get_aes_key()
    iv = os.urandom(16)  # random IV for each encryption
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode("utf-8"), BLOCK_SIZE))

    # Store iv + ciphertext together, base64-encoded
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def decrypt_private_key(token: str) -> str:
    """
    Decrypt a previously encrypted private key.
    Expects base64(iv + ciphertext).
    """
    key = _get_aes_key()
    raw = base64.b64decode(token)

    iv = raw[:16]
    ciphertext = raw[16:]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)

    return plaintext.decode("utf-8")
