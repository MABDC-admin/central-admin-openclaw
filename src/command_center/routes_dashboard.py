from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from command_center.commands import CommandRegistry
from command_center.config import get_settings

router = APIRouter()
templates = Jinja2Templates(directory="src/command_center/templates")


@router.get("/")
async def dashboard_home(request: Request):
    settings = get_settings()
    registry = CommandRegistry.default()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": settings.app_name,
            "private_access_note": settings.private_access_note,
            "commands": registry.list_commands(),
        },
    )


@router.get("/jobs")
async def jobs_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "app_name": settings.app_name,
            "jobs": [],
        },
    )
