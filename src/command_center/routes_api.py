from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from command_center.commands import CommandRegistry
from command_center.telegram_callbacks import process_telegram_callback

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@router.get("/commands")
async def list_commands() -> dict[str, list[dict[str, object]]]:
    registry = CommandRegistry.default()
    commands = [
        {
            "name": command.name,
            "description": command.description,
            "dangerous": command.dangerous,
        }
        for command in registry.list_commands()
    ]
    return {"commands": commands}


class JobSubmitRequest(BaseModel):
    command_name: str
    requested_by: str = "dashboard"
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/jobs")
async def submit_job(request: Request, job_request: JobSubmitRequest) -> dict[str, str | None]:
    result = await request.app.state.job_submission_service.submit(
        job_request.command_name,
        job_request.requested_by,
        job_request.payload,
    )
    return {
        "job_id": result.job_id,
        "status": result.status.value,
        "approval_id": result.approval_id,
    }


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, payload: dict[str, Any]) -> dict[str, bool]:
    callback = payload.get("callback_query")
    if not callback:
        return {"ok": True}

    result = await process_telegram_callback(
        callback,
        request.app.state.approval_service,
        request.app.state.telegram_client,
    )
    return {"ok": result.ok}
