"""
Alexandria Library - Authentication Routes
Minimal auth: sessions via signed cookies.
No OAuth in V1. No profiles.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import bcrypt
import secrets

from .. import templates
from ..config import settings
from ..db.database import get_db

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    # Handle legacy SHA256 hashes during migration
    if not password_hash.startswith('$2'):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def get_current_user_optional(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME)
) -> Optional[dict]:
    """
    Get current user from session cookie.
    Returns None if not logged in.
    """
    if not session_id:
        return None
    
    db = get_db()
    
    # Get session
    session = db.execute(
        """
        SELECT s.user_id, u.id, u.email, u.display_name, u.role
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = ? AND s.expires_at > datetime('now')
        """,
        (session_id,)
    ).fetchone()
    
    if not session:
        return None
    
    return dict(session)


def get_current_user_required(
    user: Optional[dict] = Depends(get_current_user_optional)
) -> dict:
    """
    Require authenticated user.
    Raises 401 if not logged in.
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Process login."""
    db = get_db()
    
    # Find user
    user = db.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Invalid email or password"
            }
        )
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    db.execute(
        """
        INSERT INTO sessions (id, user_id, expires_at)
        VALUES (?, ?, datetime('now', '+7 days'))
        """,
        (session_id, user["id"])
    )
    db.commit()
    
    # Set cookie and redirect
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.is_production
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request}
    )


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(None)
):
    """Process registration."""
    db = get_db()
    
    # Check if email exists
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Email already registered"
            }
        )
    
    # Create user
    import uuid
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    db.execute(
        """
        INSERT INTO users (id, email, password_hash, display_name, role)
        VALUES (?, ?, ?, ?, 'user')
        """,
        (user_id, email, hash_password(password), display_name)
    )
    db.commit()
    
    # Auto-login: create session
    session_id = secrets.token_urlsafe(32)
    db.execute(
        """
        INSERT INTO sessions (id, user_id, expires_at)
        VALUES (?, ?, datetime('now', '+7 days'))
        """,
        (session_id, user_id)
    )
    db.commit()
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.is_production
    )
    return response


@router.post("/logout")
async def logout(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME)
):
    """Log out - clear session."""
    if session_id:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        db.commit()
    
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    return response

