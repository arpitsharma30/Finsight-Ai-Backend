from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import get_conn
from app.security import hash_password, verify_password, new_token, utc_now_iso, expiry_iso
from app.auth import require_user


router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    name: str
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(body: SignupBody):
    conn = get_conn()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM users WHERE email = ?", (body.email.lower(),)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    pwd_hash, salt = hash_password(body.password)
    cur.execute(
        """
        INSERT INTO users(name, email, password_hash, salt, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (body.name.strip(), body.email.lower(), pwd_hash, salt, utc_now_iso()),
    )
    user_id = cur.lastrowid
    token = new_token()
    cur.execute(
        "INSERT INTO sessions(token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expiry_iso()),
    )
    conn.commit()
    conn.close()
    return {"token": token, "user": {"id": user_id, "name": body.name.strip(), "email": body.email.lower()}}


@router.post("/login")
async def login(body: LoginBody):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, name, email, password_hash, salt FROM users WHERE email = ?",
        (body.email.lower(),),
    ).fetchone()
    if not row or not verify_password(body.password, row["password_hash"], row["salt"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = new_token()
    cur.execute("INSERT INTO sessions(token, user_id, expires_at) VALUES (?, ?, ?)", (token, row["id"], expiry_iso()))
    conn.commit()
    conn.close()
    return {"token": token, "user": {"id": row["id"], "name": row["name"], "email": row["email"]}}


@router.get("/me")
async def me(user=Depends(require_user)):
    return {"user": {"id": user["id"], "name": user["name"], "email": user["email"]}}

