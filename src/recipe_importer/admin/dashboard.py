"""Admin dashboard route serving a single-page HTML dashboard."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["admin"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> HTMLResponse:
    """Serve the admin dashboard page."""
    return templates.TemplateResponse(request, "dashboard.html")
