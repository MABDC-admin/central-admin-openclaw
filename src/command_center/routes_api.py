from typing import Any

from fastapi import APIRouter, Request

from command_center.commands import CommandRegistry

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

    callback_id = str(callback.get("id", ""))
    callback_data = str(callback.get("data", ""))
    user_id = callback.get("from", {}).get("id", "unknown")

    if ":" not in callback_data:
        await request.app.state.telegram_client.answer_callback_query(
            callback_id,
            "Unsupported approval action.",
        )
        return {"ok": False}

    decision, approval_id = callback_data.split(":", 1)
    if decision not in {"approve", "reject"} or not approval_id:
        await request.app.state.telegram_client.answer_callback_query(
            callback_id,
            "Unsupported approval action.",
        )
        return {"ok": False}

    result = await request.app.state.approval_service.decide(
        approval_id,
        decision,
        f"telegram:{user_id}",
    )
    await request.app.state.telegram_client.answer_callback_query(callback_id, result.message)
    return {"ok": result.ok}
