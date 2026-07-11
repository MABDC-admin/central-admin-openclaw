from dataclasses import dataclass
from typing import Protocol


class ApprovalServiceProtocol(Protocol):
    async def decide(self, approval_id: str, decision: str, actor: str): ...


class TelegramCallbackClientProtocol(Protocol):
    async def answer_callback_query(self, callback_query_id: str, text: str) -> dict: ...


@dataclass(frozen=True)
class TelegramCallbackResult:
    ok: bool
    processed: bool


async def process_telegram_callback(
    callback: dict,
    approval_service: ApprovalServiceProtocol,
    telegram_client: TelegramCallbackClientProtocol,
) -> TelegramCallbackResult:
    callback_id = str(callback.get("id", ""))
    callback_data = str(callback.get("data", ""))
    user_id = callback.get("from", {}).get("id", "unknown")

    if ":" not in callback_data:
        await telegram_client.answer_callback_query(
            callback_id,
            "Unsupported approval action.",
        )
        return TelegramCallbackResult(ok=False, processed=False)

    decision, approval_id = callback_data.split(":", 1)
    if decision not in {"approve", "reject"} or not approval_id:
        await telegram_client.answer_callback_query(
            callback_id,
            "Unsupported approval action.",
        )
        return TelegramCallbackResult(ok=False, processed=False)

    result = await approval_service.decide(
        approval_id,
        decision,
        f"telegram:{user_id}",
    )
    await telegram_client.answer_callback_query(callback_id, result.message)
    return TelegramCallbackResult(ok=result.ok, processed=True)
