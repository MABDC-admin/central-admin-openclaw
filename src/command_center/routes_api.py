from fastapi import APIRouter

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
