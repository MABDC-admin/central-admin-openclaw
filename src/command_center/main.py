from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from command_center.approvals import ApprovalService
from command_center.config import get_settings
from command_center.db import Database
from command_center.repositories import CommandCenterRepository
from command_center.routes_api import router as api_router
from command_center.routes_dashboard import router as dashboard_router
from command_center.telegram import TelegramClient


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    db = Database(settings.database_url)
    repository = CommandCenterRepository(db)
    app.state.db = db
    app.state.repository = repository
    app.state.approval_service = ApprovalService(repository)
    if settings.telegram_configured:
        app.state.telegram_client = TelegramClient(
            settings.telegram_bot_token or "",
            settings.telegram_approval_chat_id or "",
        )
    else:
        app.state.telegram_client = TelegramClient("not-configured", "not-configured")
    app.include_router(api_router)
    app.include_router(dashboard_router)
    app.mount("/static", StaticFiles(directory="src/command_center/static"), name="static")
    return app


app = create_app()
