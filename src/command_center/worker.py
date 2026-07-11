import asyncio

from command_center.approvals import ApprovalService
from command_center.commands import CommandRegistry
from command_center.config import get_settings
from command_center.db import Database
from command_center.job_service import JobRunner
from command_center.repositories import CommandCenterRepository
from command_center.telegram import TelegramClient
from command_center.telegram_polling import TelegramApprovalPoller


async def run() -> None:
    settings = get_settings()
    db = Database(settings.database_url)
    repository = CommandCenterRepository(db)
    registry = CommandRegistry.default()
    job_runner = JobRunner(repository, registry)

    if not settings.telegram_configured:
        await job_runner.run_forever()

    approval_service = ApprovalService(repository)
    telegram_client = TelegramClient(
        settings.telegram_bot_token or "",
        settings.telegram_approval_chat_id or "",
    )
    poller = TelegramApprovalPoller(telegram_client, approval_service)
    await asyncio.gather(
        job_runner.run_forever(),
        poller.run_forever(),
    )


def main() -> None:
    while True:
        asyncio.run(run())


if __name__ == "__main__":
    main()
