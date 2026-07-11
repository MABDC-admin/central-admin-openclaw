import os
import shutil
import socket
from dataclasses import dataclass
from typing import Any, Callable

from command_center.models import CommandDefinition

CommandHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredCommand:
    definition: CommandDefinition
    handler: CommandHandler

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def dangerous(self) -> bool:
        return self.definition.dangerous


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, RegisteredCommand] = {}

    def register(self, definition: CommandDefinition, handler: CommandHandler) -> None:
        self._commands[definition.name] = RegisteredCommand(definition=definition, handler=handler)

    def get(self, name: str) -> RegisteredCommand:
        if name not in self._commands:
            raise KeyError(f"Unknown command: {name}")
        return self._commands[name]

    def list_commands(self) -> list[CommandDefinition]:
        return [registered.definition for registered in self._commands.values()]

    @classmethod
    def default(cls) -> "CommandRegistry":
        registry = cls()
        registry.register(
            CommandDefinition(
                name="vps.health",
                description="Read-only VPS health summary",
                dangerous=False,
            ),
            lambda payload: run_vps_health_check(),
        )
        return registry


def run_vps_health_check() -> dict[str, Any]:
    total, used, free = shutil.disk_usage("/")
    load_avg = os.getloadavg()

    return {
        "ok": True,
        "hostname": socket.gethostname(),
        "disk_root": {
            "total_gb": round(total / 1024 / 1024 / 1024, 2),
            "used_gb": round(used / 1024 / 1024 / 1024, 2),
            "free_gb": round(free / 1024 / 1024 / 1024, 2),
        },
        "load_average": {
            "one_minute": load_avg[0],
            "five_minutes": load_avg[1],
            "fifteen_minutes": load_avg[2],
        },
    }
