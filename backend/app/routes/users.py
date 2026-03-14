from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

router = APIRouter()

# Use pbkdf2_sha256 to avoid bcrypt compatibility issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

users = [
    {
        "id": 1,
        "name": "Admin",
        "email": "admin@portal.com",
        "password_hash": pwd_context.hash("Admin123!"),
        "role": "admin"
    }
]


def get_user_by_email(email: str):
    for user in users:
        if user["email"].lower() == email.lower():
            return user
    return None


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

    new_user = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password_hash": pwd_context.hash(password),
        "role": role
    }

    users.append(new_user)

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