# Central Admin OpenClaw

Private single-user automation command center for MABDC.

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
uvicorn command_center.main:app --app-dir src --reload --port 8088
```

## Safety model

Destructive actions require Telegram approval. The foundation build only includes read-only commands and approval primitives.

Telegram approval uses outbound long polling from the VPS worker. This keeps the command center hidden on Tailscale/ZeroTier and avoids exposing a public webhook URL.

Required Telegram settings in `deploy/command-center.env`:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_APPROVAL_CHAT_ID=your_private_chat_id
```

## Deployment target

The approved deployment path is `/DATA/docker/command-center` on the aaPanel VPS.
