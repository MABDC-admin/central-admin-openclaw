from typing import Any

from fastapi import APIRouter, Request

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
