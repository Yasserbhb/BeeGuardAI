"""
BeeGuardAI - Auth Routes
"""

import hashlib
import secrets
from fastapi import APIRouter, HTTPException, Request, Response
from app.models import UserRegister, UserLogin
from app.db.mysql import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_session(user_id: int, email: str, role: str, org_id: int) -> str:
    token = secrets.token_hex(32)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (token, user_id, email, role, organisation_id)
        VALUES (%s, %s, %s, %s, %s)
    ''', (token, user_id, email, role, org_id))
    conn.close()
    return token


def get_current_user(request: Request):
    """Get current authenticated user from request"""
    token = request.cookies.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE token = %s", (token,))
    session = cursor.fetchone()
    conn.close()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return session


@router.post("/register")
async def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM utilisateurs WHERE email = %s", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    cursor.execute("SELECT id FROM organisations WHERE nom = %s", (user.organisation_nom,))
    org = cursor.fetchone()

    if org:
        org_id = org["id"]
    else:
        cursor.execute("INSERT INTO organisations (nom) VALUES (%s)", (user.organisation_nom,))
        org_id = cursor.lastrowid

    password_hash = hash_password(user.mot_de_passe)
    cursor.execute('''
        INSERT INTO utilisateurs (email, mot_de_passe, nom, prenom, role, organisation_id)
        VALUES (%s, %s, %s, %s, 'admin', %s)
    ''', (user.email, password_hash, user.nom, user.prenom, org_id))

    conn.close()
    return {"success": True, "message": "User registered successfully"}


@router.post("/login")
async def login(user: UserLogin, response: Response):
    conn = get_db()
    cursor = conn.cursor()

    password_hash = hash_password(user.mot_de_passe)
    cursor.execute('''
        SELECT id, email, nom, prenom, role, organisation_id
        FROM utilisateurs
        WHERE email = %s AND mot_de_passe = %s
    ''', (user.email, password_hash))

    db_user = cursor.fetchone()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_session(db_user["id"], db_user["email"], db_user["role"], db_user["organisation_id"])

    response.set_cookie(key="token", value=token, httponly=True, max_age=86400)
    return {"success": True, "token": token, "user": db_user}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("token")

    if token:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.close()

    response.delete_cookie("token")
    return {"success": True}


@router.get("/me")
async def get_me(request: Request):
    user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.email, u.nom, u.prenom, u.role, o.nom as organisation_nom
        FROM utilisateurs u
        LEFT JOIN organisations o ON u.organisation_id = o.id
        WHERE u.id = %s
    ''', (user["user_id"],))

    db_user = cursor.fetchone()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user
