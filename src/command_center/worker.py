import asyncio

from command_center.approvals import ApprovalService
from command_center.config import get_settings
from command_center.db import Database
from command_center.repositories import CommandCenterRepository
from command_center.telegram import TelegramClient
from command_center.telegram_polling import TelegramApprovalPoller


async def run() -> None:
    settings = get_settings()
    if not settings.telegram_configured:
        while True:
            await asyncio.sleep(30)

    db = Database(settings.database_url)
    repository = CommandCenterRepository(db)
    approval_service = ApprovalService(repository)
    telegram_client = TelegramClient(
        settings.telegram_bot_token or "",
        settings.telegram_approval_chat_id or "",
    )
    poller = TelegramApprovalPoller(telegram_client, approval_service)
    await poller.run_forever()


def main() -> None:
    while True:
        asyncio.run(run())


if __name__ == "__main__":
    main()
