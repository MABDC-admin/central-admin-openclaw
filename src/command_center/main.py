from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from command_center.config import get_settings
from command_center.routes_api import router as api_router
from command_center.routes_dashboard import router as dashboard_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    app.include_router(dashboard_router)
    app.mount("/static", StaticFiles(directory="src/command_center/static"), name="static")
    return app


app = create_app()
