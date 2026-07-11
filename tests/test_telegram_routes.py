from fastapi.testclient import TestClient

from command_center.main import create_app


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
    def __init__(self):
        self.answers = []

    async def answer_callback_query(self, callback_query_id, text):
        self.answers.append((callback_query_id, text))
        return {"ok": True}


def callback_payload(data="approve:approval-1"):
    return {
        "callback_query": {
            "id": "callback-1",
            "from": {"id": 123},
            "data": data,
        }
    }


def test_telegram_webhook_approves_callback():
    app = create_app()
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient()
    app.state.approval_service = approval_service
    app.state.telegram_client = telegram_client
    client = TestClient(app)

    response = client.post("/api/telegram/webhook", json=callback_payload())

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert approval_service.calls == [("approval-1", "approve", "telegram:123")]
    assert telegram_client.answers == [("callback-1", "Approved.")]


def test_telegram_webhook_rejects_callback():
    app = create_app()
    approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient()
    app.state.approval_service = approval_service
    app.state.telegram_client = telegram_client
    client = TestClient(app)

    response = client.post("/api/telegram/webhook", json=callback_payload("reject:approval-1"))

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert approval_service.calls == [("approval-1", "reject", "telegram:123")]
    assert telegram_client.answers == [("callback-1", "Rejected.")]


def test_telegram_webhook_ignores_unknown_callback_format():
    app = create_app()
    app.state.approval_service = FakeApprovalService()
    telegram_client = FakeTelegramClient()
    app.state.telegram_client = telegram_client
    client = TestClient(app)

    response = client.post("/api/telegram/webhook", json=callback_payload("unknown"))

    assert response.status_code == 200
    assert response.json() == {"ok": False}
    assert telegram_client.answers == [("callback-1", "Unsupported approval action.")]


def test_telegram_webhook_ignores_non_callback_payload():
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/telegram/webhook", json={"message": {"text": "hello"}})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
