from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.routes.maintenance import router as maintenance_router
from app.routes.payments import router as payments_router
from app.routes.users import router as users_router

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-this-later")

app.include_router(maintenance_router)
app.include_router(payments_router)
app.include_router(users_router)

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