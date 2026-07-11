# OpenClaw Monorepo Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Central Admin OpenClaw into a lightweight project monorepo without changing its runtime behavior, private access, database, or approval controls.

**Architecture:** Keep the FastAPI API and worker as one application under `projects/command-center/apps/api/`. Put shared agent policy at the root and isolate Gmail, PC nodes, VPS browser automation, and Nextcloud watcher in project folders. Root commands provide stable verification after paths change.

**Tech Stack:** Python 3.12, FastAPI, pytest, Ruff, Docker Compose, PostgreSQL/Supabase, Bash, OpenClaw Markdown

---

## File Map

- Move: `.env.example`, `pyproject.toml`, `src/`, `tests/`, `migrations/`, `deploy/` to `projects/command-center/apps/api/`.
- Create: root `.openclaw/` policy files and shared `crons/` and `skills/` guidance.
- Create: project `.openclaw/AGENT.md` files for command center, Gmail, PC nodes, browser automation, and Nextcloud watcher.
- Create: `Makefile`, `scripts/check-layout.sh`, and `scripts/smoke-command-center.sh`.
- Create: `docs/operations/command-center-baseline.md`.
- Modify: `README.md`, `.gitignore`, and the moved deployment README.

### Task 1: Capture The Production Baseline

**Files:**
- Create: `docs/operations/command-center-baseline.md`

- [ ] **Step 1: Verify the current tree**

```bash
pytest -v
ruff check src tests
docker compose -f deploy/docker-compose.yml config --quiet
docker compose -f deploy/docker-compose.yml build
```

Expected: 33 tests pass; lint, Compose validation, and both builds exit 0.

- [ ] **Step 2: Record live state without reading secrets**

```bash
ssh -i /tmp/codex-ssh/minio_root_ed25519 -p 1988 root@100.124.32.11 \
  "cd /DATA/docker/command-center/app && docker compose -f deploy/docker-compose.yml ps && \
   docker inspect -f '{{.Image}}' deploy-command-center-api-1 deploy-command-center-worker-1"
curl --fail --silent --show-error http://100.124.32.11:18088/health
```

Write the date, commit `4e88338`, URL, VPS path, container names, image IDs, `supabase_default` network, and rollback commit to the baseline document. State explicitly that no environment values were recorded.

- [ ] **Step 3: Commit**

```bash
git add docs/operations/command-center-baseline.md
git commit -m "docs: record command center production baseline"
```

### Task 2: Add A Failing Layout Check

**Files:**
- Create: `scripts/check-layout.sh`
- Create: `Makefile`

- [ ] **Step 1: Write the layout test**

```bash
#!/usr/bin/env bash
set -euo pipefail

required=(
  ".openclaw/AGENTS.md"
  ".openclaw/SOUL.md"
  ".openclaw/USER.md"
  ".openclaw/MEMORY.md"
  ".openclaw/HEARTBEAT.md"
  "projects/command-center/.openclaw/AGENT.md"
  "projects/command-center/apps/api/pyproject.toml"
  "projects/command-center/apps/api/src/command_center/main.py"
  "projects/command-center/apps/api/tests/test_routes.py"
  "projects/command-center/apps/api/deploy/docker-compose.yml"
  "projects/gmail/.openclaw/AGENT.md"
  "projects/pc-nodes/.openclaw/AGENT.md"
  "projects/browser-automation/.openclaw/AGENT.md"
  "projects/nextcloud-doc-watcher/.openclaw/AGENT.md"
)
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "missing required monorepo file: $path" >&2; exit 1; }
done
echo "monorepo layout verified"
```

Run `chmod +x scripts/check-layout.sh && ./scripts/check-layout.sh`.
Expected: FAIL on `.openclaw/AGENTS.md`.

- [ ] **Step 2: Add root commands**

```makefile
API_DIR := projects/command-center/apps/api
COMPOSE_FILE := $(API_DIR)/deploy/docker-compose.yml

.PHONY: install test lint layout compose-config build verify
install:
	python3.12 -m pip install -e "$(API_DIR)[dev]"
test:
	python3.12 -m pytest -c $(API_DIR)/pyproject.toml $(API_DIR)/tests -v
lint:
	python3.12 -m ruff check --config $(API_DIR)/pyproject.toml $(API_DIR)/src $(API_DIR)/tests
layout:
	./scripts/check-layout.sh
compose-config:
	docker compose -f $(COMPOSE_FILE) config --quiet
build:
	docker compose -f $(COMPOSE_FILE) build
verify: layout test lint compose-config
```

- [ ] **Step 3: Commit**

```bash
git add Makefile scripts/check-layout.sh
git commit -m "test: define required monorepo layout"
```

### Task 3: Create OpenClaw Boundaries

**Files:**
- Create: `.openclaw/{AGENTS,SOUL,USER,MEMORY,HEARTBEAT}.md`
- Create: `.openclaw/crons/README.md` and `.openclaw/skills/README.md`
- Create: each project `.openclaw/AGENT.md` and `data/README.md`

- [ ] **Step 1: Add global policy**

```markdown
<!-- .openclaw/AGENTS.md -->
# Global Agent Policy

This is a private, single-user MABDC automation workspace. Load global policy, then only the
active project's AGENT.md. Keep credentials in protected runtime environment files. Commands
that delete data, send messages, alter accounts, install software, or execute privileged changes
require one-time Telegram approval for the exact job payload.
```

Create `SOUL.md` requiring evidence-driven operation and forbidding approval or network bypass.
Create `USER.md` naming one authorized MABDC IT operator while retaining mandatory approvals.
Create `MEMORY.md` forbidding secrets, raw email, tokens, and keys.
Create `HEARTBEAT.md` limiting periodic checks to read-only reporting.
Global crons may only mutate state by creating approval-gated jobs; global skills must be reusable by at least two projects.

- [ ] **Step 2: Add project policies**

- Command center owns FastAPI, worker, Supabase repositories, approvals, audit logs, commands, and Docker. Tailscale binding and `supabase_default` are invariants.
- Gmail owns OAuth onboarding, account registry, mailbox commands, and schedules. Tokens cannot be committed; destructive mailbox actions require approval.
- PC nodes use the VPS dispatcher and Windows agent/OpenSSH over ZeroTier/Tailscale. Privileged actions require local enforcement, audit, and approval.
- Browser automation runs on the VPS only. Sends, purchases, uploads, deletes, and account changes require approval.
- Nextcloud owns watcher, dispatcher, service, extensions, and mail API contract. Inventory scripts and remove embedded secrets before import.

Each `data/README.md` permits schemas and redacted examples only. Add project-local skills/crons README files where shown in the approved design.

- [ ] **Step 3: Verify and commit**

Run `./scripts/check-layout.sh`.
Expected: FAIL only because `projects/command-center/apps/api/pyproject.toml` is not moved yet.

```bash
git add .openclaw projects
git commit -m "docs: add OpenClaw project boundaries"
```

### Task 4: Move The Command Center Application

**Files:**
- Move: `.env.example`, `pyproject.toml`, `src/`, `tests/`, `migrations/`, `deploy/`
- Create: `projects/command-center/apps/api/README.md`
- Modify: `.gitignore` and moved `deploy/README.md`

- [ ] **Step 1: Move with history**

```bash
mkdir -p projects/command-center/apps/api
git mv .env.example pyproject.toml src tests migrations deploy projects/command-center/apps/api/
```

Create `projects/command-center/apps/api/README.md` with the existing local setup, safety model,
Telegram settings, and deployment-target sections from the root README. The later root README
becomes the workspace overview.

- [ ] **Step 2: Protect nested environments**

```gitignore
.env
.env.*
**/.env
**/.env.*
!**/.env.example
!**/command-center.env.example
**/command-center.env
```

Keep all existing Python, test, coverage, and build ignores.

- [ ] **Step 3: Preserve Docker resolution**

The moved Compose build remains:

```yaml
build:
  context: ..
  dockerfile: deploy/runtime.Dockerfile
```

The copied API README keeps `COPY pyproject.toml README.md /app/` valid. Update deployment docs to use `projects/command-center/apps/api/deploy/docker-compose.yml` and preserve the nested `command-center.env`.

- [ ] **Step 4: Verify and commit**

```bash
make layout
make install
make test
make lint
make compose-config
make build
git add .gitignore projects/command-center/apps/api
git commit -m "refactor: move command center into monorepo"
```

Expected: layout passes, 33 tests pass, lint and Compose pass, and both images build.

### Task 5: Add Root Documentation And Live Smoke Test

**Files:**
- Modify: `README.md`
- Create: `scripts/smoke-command-center.sh`

- [ ] **Step 1: Document the workspace**

Document all five project folders, root `make` commands, private URL, Tailscale-only access, Telegram approval, and no-secrets rule. Mark Gmail, PC-node, browser, and Nextcloud folders as future implementation boundaries.

- [ ] **Step 2: Write the smoke test**

```bash
#!/usr/bin/env bash
set -euo pipefail
base_url="${COMMAND_CENTER_URL:-http://100.124.32.11:18088}"
curl --fail --silent --show-error "$base_url/health" >/dev/null
job_json="$(curl --fail --silent --show-error -H 'Content-Type: application/json' \
  -d '{"command_name":"vps.health","payload":{}}' "$base_url/api/jobs")"
printf '%s' "$job_json" | python3 -c '
import json, sys
response = json.load(sys.stdin)
assert response["job_id"], response
assert response["status"] in {"pending", "running", "succeeded"}, response
print(response["job_id"])
'
```

- [ ] **Step 3: Confirm the API contract**

Run `rg -n 'api/jobs|JobRead|command_name' projects/command-center/apps/api/src projects/command-center/apps/api/tests`.
Expected: the contract confirms `POST /api/jobs` returns `job_id`, `status`, and `approval_id`.
Change only the smoke script if those tested fields differ; do not add a new API route.

- [ ] **Step 4: Verify and commit**

```bash
chmod +x scripts/smoke-command-center.sh
make verify
make build
git diff --check
git add README.md scripts/smoke-command-center.sh
git commit -m "docs: document monorepo operations"
```

### Task 6: Deploy With Rollback Protection

**Files:**
- Replace on VPS: `/DATA/docker/command-center/app/`
- Preserve: production environment and timestamped source backup
- Modify: `docs/operations/command-center-baseline.md`

- [ ] **Step 1: Final local proof and push**

Run `make verify && make build && git status --short`, requiring a clean tree and all checks passing. Then run `git push origin main`.

- [ ] **Step 2: Back up production**

Create `/DATA/docker/command-center/backups/2026-07-11-before-monorepo/` containing current source, Compose files, and environment file. Do not print the environment.

- [ ] **Step 3: Stage and build**

Stage the pushed tree at `/DATA/docker/command-center/staging-monorepo` and restore the protected environment to `projects/command-center/apps/api/deploy/command-center.env` inside it.

```bash
docker compose -f /DATA/docker/command-center/staging-monorepo/projects/command-center/apps/api/deploy/docker-compose.yml build
```

Expected: both images build while old containers remain running.

- [ ] **Step 4: Switch and verify**

Move staged source to `/DATA/docker/command-center/app`, retain the backup, and run:

```bash
docker compose -f /DATA/docker/command-center/app/projects/command-center/apps/api/deploy/docker-compose.yml up -d
docker compose -f /DATA/docker/command-center/app/projects/command-center/apps/api/deploy/docker-compose.yml ps
job_id="$(COMMAND_CENTER_URL=http://100.124.32.11:18088 ./scripts/smoke-command-center.sh)"
curl --fail --silent --show-error http://100.124.32.11:18088/ >/dev/null
```

Poll that exact job in Supabase from the VPS without reading environment values:

```bash
ssh -i /tmp/codex-ssh/minio_root_ed25519 -p 1988 root@100.124.32.11 \
  "docker exec supabase-db psql -U postgres -d postgres -Atc \
  \"select status from command_center.jobs where id = '$job_id';\""
```

Expected: the submitted job reaches `succeeded`. Check logs for startup exceptions and compare
`command_center` table counts before and after; no count may decrease.

- [ ] **Step 5: Roll back on any failure**

Restore the backup and original environment, run its original `deploy/docker-compose.yml`, then repeat health and `vps.health` checks. Stop the migration until the failure is separately diagnosed.

- [ ] **Step 6: Record evidence**

Add deployed commit, time, new image IDs, successful smoke-job ID, and backup path to the baseline document, then commit and push it.

## Completion Criteria

- Approved global and project boundaries exist.
- Original 33 tests pass from the nested path.
- Layout, lint, Compose, Docker, and whitespace checks pass.
- Production remains private at `http://100.124.32.11:18088`.
- API and worker use the existing Supabase data.
- A new `vps.health` job succeeds.
- A complete rollback backup is retained.
- No Gmail, PC-node, browser, or Nextcloud behavior is added.
