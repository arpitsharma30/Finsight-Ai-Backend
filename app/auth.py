from datetime import datetime, timezone
from fastapi import Header, HTTPException
from app.db import get_conn


def require_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT s.user_id, s.expires_at, u.name, u.email
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
        """,
        (token,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires = datetime.fromisoformat(row["expires_at"])
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    return {
        "id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "token": token,
    }

