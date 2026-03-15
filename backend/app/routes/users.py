from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from app.database import get_connection

router = APIRouter()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()

    conn.close()

    return dict(row) if row else None


def ensure_admin_exists():
    existing_admin = get_user_by_email("admin@portal.com")
    if existing_admin:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, (
        "Admin",
        "admin@portal.com",
        pwd_context.hash("Admin123!"),
        "admin"
    ))

    conn.commit()
    conn.close()


# IMPORTANT: seed admin immediately when file loads
ensure_admin_exists()


@router.post("/signup")
def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    existing_user = get_user_by_email(email)
    if existing_user:
        return RedirectResponse(url="/login", status_code=303)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        email,
        pwd_context.hash(password),
        role
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/login", status_code=303)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    user = get_user_by_email(email)

    if not user or not pwd_context.verify(password, user["password_hash"]):
        return RedirectResponse(url="/login", status_code=303)

    request.session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }

    if user["role"] == "tenant":
        return RedirectResponse(url="/tenant/dashboard", status_code=303)
    elif user["role"] == "owner":
        return RedirectResponse(url="/owner/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
