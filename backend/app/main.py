from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import os

from app.routes.maintenance import router as maintenance_router
from app.routes.payments import router as payments_router
from app.routes.properties import router as properties_router
from app.database import init_db
from app.routes.users import router as users_router

app = FastAPI()

init_db()

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret")
)

app.include_router(maintenance_router)
app.include_router(payments_router)
app.include_router(users_router)
app.include_router(properties_router)


templates = Jinja2Templates(directory="app/templates")


def require_role(request: Request, allowed_roles: list):
    user = request.session.get("user")
    if not user or user["role"] not in allowed_roles:
        return None
    return user


@app.get("/")
def root():
    return RedirectResponse(url="/login")


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/tenant/dashboard")
def tenant_dashboard(request: Request):
    user = require_role(request, ["tenant"])
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "tenant_dashboard.html",
        {"request": request, "user": user}
    )


@app.get("/owner/dashboard")
def owner_dashboard(request: Request):
    user = require_role(request, ["owner"])
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "owner_dashboard.html",
        {"request": request, "user": user}
    )


@app.get("/admin/dashboard")
def admin_dashboard(request: Request):
    user = require_role(request, ["admin"])
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "user": user}
    )
from app.database import get_connection
from fastapi import HTTPException
@app.get("/receipt/{payment_id}")
def receipt_page(request: Request, payment_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Receipt not found")

    payment = dict(row)

    return templates.TemplateResponse(
        "receipt.html",
        {"request": request, "payment": payment}
    )
