import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal, get_db
from backend.app.models import UserModel, UserSessionModel

router = APIRouter(prefix="/auth", tags=["Authentication"])
SESSION_COOKIE = "detectiveai_session"
SESSION_DAYS = 7
PBKDF2_ITERATIONS = 310_000


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)
    confirm_password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    return normalized


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, _iterations, salt_hex, expected = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        actual = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 3)[3]
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(user: UserModel) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _set_session(response: Response, user: UserModel, db: Session) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    db.add(UserSessionModel(user_id=user.id, token_hash=_token_hash(token), expires_at=expires))
    db.commit()
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 24 * 60 * 60,
                        httponly=True, secure=settings.AUTH_COOKIE_SECURE, samesite="lax", path="/")


def authenticated_user(token: Optional[str], db: Session) -> Optional[UserModel]:
    if not token:
        return None
    session = db.query(UserSessionModel).filter(UserSessionModel.token_hash == _token_hash(token)).first()
    if not session:
        return None
    if session.expires_at <= datetime.utcnow():
        db.delete(session)
        db.commit()
        return None
    return session.user


@router.post("/register")
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=422, detail="Enter your full name.")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    email = _email(payload.email)
    if db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = UserModel(full_name=full_name, email=email, password_hash=_hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)
    _set_session(response, user, db)
    return {"user": _public_user(user)}


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = _email(payload.email)
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _set_session(response, user, db)
    return {"user": _public_user(user)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        session = db.query(UserSessionModel).filter(UserSessionModel.token_hash == _token_hash(token)).first()
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=settings.AUTH_COOKIE_SECURE, samesite="lax")
    return {"status": "logged_out"}


@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request.cookies.get(SESSION_COOKIE), db)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return {"user": _public_user(user)}


def require_authenticated_request(request: Request) -> Optional[dict]:
    path = request.url.path
    if not path.startswith("/api/") or path == "/api/health" or path.startswith("/api/auth/") or request.method == "OPTIONS":
        return None
    db = SessionLocal()
    try:
        user = authenticated_user(request.cookies.get(SESSION_COOKIE), db)
        return _public_user(user) if user else None
    finally:
        db.close()
