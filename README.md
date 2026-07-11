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

## Deployment target

The approved deployment path is `/DATA/docker/command-center` on the aaPanel VPS.
