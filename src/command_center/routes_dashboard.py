from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
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
    try:
        jobs = await request.app.state.repository.list_recent_jobs()
    except Exception:
        jobs = []
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "app_name": settings.app_name,
            "jobs": jobs,
        },
    )


@router.post("/jobs")
async def create_job_from_dashboard(
    request: Request,
    command_name: str = Form(...),
):
    await request.app.state.job_submission_service.submit(
        command_name,
        "dashboard",
        {},
    )
    return RedirectResponse("/jobs", status_code=303)
