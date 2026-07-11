from command_center.telegram_polling import TelegramApprovalPoller


class FakeApprovalService:
    def __init__(self):
        self.calls = []

    async def decide(self, approval_id, decision, actor):
        self.calls.append((approval_id, decision, actor))
        return type(
            "Result",
            (),
            {
                "ok": True,
                "message": "Approved." if decision == "approve" else "Rejected.",
            },
        )()


class FakeTelegramClient:
    def __init__(self, updates):
        self.updates = list(updates)
        self.answers = []
        self.offsets = []

    async def get_updates(self, offset=None, timeout=25):
        self.offsets.append((offset, timeout))
        if self.updates:
            return {"ok": True, "result": self.updates.pop(0)}
        return {"ok": True, "result": []}

    async def answer_callback_query(self, callback_query_id, text):
        self.answers.append((callback_query_id, text))
        return {"ok": True}


def callback_update(update_id=10, data="approve:approval-1", user_id=123):
    return {
        "update_id": update_id,
        "callback_query": {
            "id": "callback-1",
            "from": {"id": user_id},
            "data": data,
        },
    }


async def test_poll_once_processes_approval_callback():
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient([[callback_update()]])
    poller = TelegramApprovalPoller(telegram_client, approval_service)

    processed = await poller.poll_once()

    assert processed == 1
    assert poller.offset == 11
    assert approval_service.calls == [("approval-1", "approve", "telegram:123")]
    assert telegram_client.answers == [("callback-1", "Approved.")]


async def test_poll_once_rejects_approval_callback():
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient([[callback_update(data="reject:approval-1")]])
    poller = TelegramApprovalPoller(telegram_client, approval_service)

    processed = await poller.poll_once()

    assert processed == 1
    assert approval_service.calls == [("approval-1", "reject", "telegram:123")]
    assert telegram_client.answers == [("callback-1", "Rejected.")]


async def test_poll_once_ignores_non_callback_updates_but_advances_offset():
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient([[{"update_id": 20, "message": {"text": "hello"}}]])
    poller = TelegramApprovalPoller(telegram_client, approval_service)

    processed = await poller.poll_once()

    assert processed == 0
    assert poller.offset == 21
    assert approval_service.calls == []
    assert telegram_client.answers == []


async def test_poll_once_answers_unsupported_callback():
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient([[callback_update(data="unknown")]])
    poller = TelegramApprovalPoller(telegram_client, approval_service)

    processed = await poller.poll_once()

    assert processed == 0
    assert approval_service.calls == []
    assert telegram_client.answers == [("callback-1", "Unsupported approval action.")]
