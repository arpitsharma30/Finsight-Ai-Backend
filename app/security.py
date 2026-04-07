import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or base64.b64encode(secrets.token_bytes(16)).decode("utf-8")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    )
    return base64.b64encode(digest).decode("utf-8"), salt


def verify_password(password: str, expected_hash: str, salt: str) -> bool:
    got_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(got_hash, expected_hash)


def new_token() -> str:
    return secrets.token_urlsafe(40)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def expiry_iso(days: int = 14) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

