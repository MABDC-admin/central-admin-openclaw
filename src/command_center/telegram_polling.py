import asyncio

from command_center.telegram_callbacks import process_telegram_callback


class TelegramApprovalPoller:
    def __init__(
        self,
        telegram_client,
        approval_service,
        offset: int | None = None,
        poll_timeout: int = 25,
    ) -> None:
        self.telegram_client = telegram_client
        self.approval_service = approval_service
        self.offset = offset
        self.poll_timeout = poll_timeout

    async def poll_once(self) -> int:
        response = await self.telegram_client.get_updates(
            offset=self.offset,
            timeout=self.poll_timeout,
        )
        updates = response.get("result", [])
        processed = 0
        for update in updates:
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                self.offset = update_id + 1

            callback = update.get("callback_query")
            if not callback:
                continue

            result = await process_telegram_callback(
                callback,
                self.approval_service,
                self.telegram_client,
            )
            if result.processed:
                processed += 1

        return processed

    async def run_forever(self, sleep_seconds: float = 2.0) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception:
                await asyncio.sleep(sleep_seconds)
            else:
                await asyncio.sleep(0)
