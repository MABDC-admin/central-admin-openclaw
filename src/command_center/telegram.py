from typing import Any

import httpx


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_approval_request(
        self,
        text: str,
        approval_id: str,
    ) -> dict[str, Any]:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "Approve", "callback_data": f"approve:{approval_id}"},
                        {"text": "Reject", "callback_data": f"reject:{approval_id}"},
                    ]
                ]
            },
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            return response.json()
