"""
Server-rendered page routes (Jinja2). These render the shell for each
screen; the pages themselves fetch data from the JSON API via app.js.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.models.user import User

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, user: User | None, **extra):
    return {"request": request, "user": user, **extra}


@router.get("/", response_class=HTMLResponse)
def landing(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", _ctx(request, None))


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", _ctx(request, None))


def _require_login(user: User | None):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return None


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("dashboard.html", _ctx(request, user, active="dashboard"))


@router.get("/transactions", response_class=HTMLResponse)
def transactions_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("transactions.html", _ctx(request, user, active="transactions"))


@router.get("/accounts", response_class=HTMLResponse)
def accounts_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("accounts.html", _ctx(request, user, active="accounts"))


@router.get("/budgets", response_class=HTMLResponse)
def budgets_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("budgets.html", _ctx(request, user, active="budgets"))


@router.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("reports.html", _ctx(request, user, active="reports"))


@router.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("categories.html", _ctx(request, user, active="categories"))


@router.get("/notifications", response_class=HTMLResponse)
def notifications_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("notifications.html", _ctx(request, user, active="notifications"))


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return templates.TemplateResponse("settings.html", _ctx(request, user, active="settings"))
