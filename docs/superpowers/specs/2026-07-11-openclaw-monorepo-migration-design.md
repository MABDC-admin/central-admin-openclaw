# OpenClaw Monorepo Migration Design

## Status

Approved design. This document defines the migration; implementation has not started.

## Goal

Restructure Central Admin OpenClaw into a lightweight OpenClaw monorepo while preserving
the behavior, data, access controls, and deployment of the running command center. The new
layout will give each automation area clear ownership of its instructions, skills, schedules,
application code, and operational data.

The structure is inspired by Jonathan Gelin's OpenClaw monorepo article:
<https://smartsdlc.dev/blog/you-should-start-your-openclaw-monorepo/>.

## Current Production Baseline

- Repository baseline: commit `4e88338`.
- Runtime: FastAPI API and Python worker in Docker Compose.
- Production directory: `/DATA/docker/command-center/app` on the aaPanel VPS.
- Private dashboard: `http://100.124.32.11:18088`, bound to Tailscale.
- Database: existing Supabase PostgreSQL container and `command_center` schema.
- Existing behavior: dashboard, job submission, command registry, worker execution,
  Telegram approval primitives, and the read-only `vps.health` command.
- Production secrets remain in the server-side environment file and are never committed.

## Decisions

1. Use a lightweight folder-based monorepo now. Do not introduce Nx until the repository
   contains multiple buildable JavaScript or TypeScript packages that benefit from dependency
   graphs, affected builds, or build caching.
2. Preserve the command center as one deployable Python application during this migration.
   This is an organizational change, not a service rewrite.
3. Give every automation domain its own project folder and `.openclaw/AGENT.md` context.
4. Keep shared assistant policy, reusable skills, global schedules, and global memory under the
   root `.openclaw/` folder.
5. Keep runtime state in Supabase or external service storage. Repository `data/` folders hold
   schemas, examples, operational documentation, and non-secret versioned data only.
6. Dangerous actions continue to require explicit approval through the private Telegram bot.
7. The dashboard remains private on Tailscale/ZeroTier. This migration creates no public route.

## Target Structure

```text
central-admin-openclaw/
|-- .openclaw/
|   |-- AGENTS.md
|   |-- SOUL.md
|   |-- USER.md
|   |-- MEMORY.md
|   |-- HEARTBEAT.md
|   |-- crons/
|   `-- skills/
|-- projects/
|   |-- command-center/
|   |   |-- .openclaw/
|   |   |   `-- AGENT.md
|   |   |-- apps/
|   |   |   `-- api/
|   |   |       |-- src/
|   |   |       |-- tests/
|   |   |       |-- migrations/
|   |   |       |-- deploy/
|   |   |       `-- pyproject.toml
|   |   `-- data/
|   |-- gmail/
|   |   |-- .openclaw/
|   |   |   |-- AGENT.md
|   |   |   |-- crons/
|   |   |   `-- skills/
|   |   `-- data/
|   |-- pc-nodes/
|   |   |-- .openclaw/
|   |   |   |-- AGENT.md
|   |   |   `-- skills/
|   |   `-- data/
|   |-- browser-automation/
|   |   |-- .openclaw/
|   |   |   |-- AGENT.md
|   |   |   `-- skills/
|   |   `-- data/
|   `-- nextcloud-doc-watcher/
|       |-- .openclaw/
|       |   |-- AGENT.md
|       |   `-- skills/
|       |-- scripts/
|       `-- data/
|-- docs/
|-- scripts/
|-- .env.example
|-- .gitignore
`-- README.md
```

## Project Responsibilities

### Command Center

Owns the FastAPI dashboard, API, worker, approval engine, command registry, database migrations,
and Docker deployment. Other projects integrate through its command and job interfaces rather
than importing its internal modules.

### Gmail

Owns Gmail OAuth account definitions, mailbox commands, Gmail-specific schedules, and account
onboarding guidance. OAuth tokens remain encrypted or in server-managed secrets; they are not
stored in repository data files.

### PC Nodes

Owns Windows node registration, ZeroTier/Tailscale connectivity metadata, allowed local actions,
and node-agent or OpenSSH integration. The command center remains the central dispatcher.

### Browser Automation

Owns VPS-only browser sessions, browser commands, session lifecycle rules, and browser-specific
diagnostics. It does not control browsers on office PCs.

### Nextcloud Document Watcher

Owns the watcher and email-dispatcher source, service documentation, supported file rules, and
integration contract with the mail API. Existing production scripts are inventoried before any
replacement. Mail API credentials are moved to protected environment variables and rotated if
they were previously embedded in source.

## Runtime Flow

1. A user submits a common command from the dashboard or Telegram.
2. The command center validates the command and records a job in Supabase.
3. Safe read-only commands may run immediately through the worker.
4. Dangerous or destructive commands enter `pending_approval` and are sent to the private
   Telegram approval chat.
5. Approval allows one execution of that exact job payload. Rejection closes the job without
   execution.
6. The appropriate project adapter performs the Gmail, VPS, PC-node, browser, file, or service
   operation and writes the result and audit record back to Supabase.

The monorepo changes where code and instructions live; it does not weaken this control flow.

## Migration Sequence

1. Capture the current local and production baseline, including tests, image builds, containers,
   private URL, database connectivity, and a successful `vps.health` job.
2. Add the root `.openclaw/` policy structure and empty domain project boundaries with concise
   ownership documents.
3. Move the existing Python application into `projects/command-center/apps/api/` and update only
   path-dependent packaging, tests, Docker build context, and documentation.
4. Add root helper commands for test, lint, build, and deployment so operators do not need to
   remember nested paths.
5. Run local tests, lint, and Docker image builds from a clean checkout.
6. Package the verified tree and deploy it to the existing VPS application directory while
   preserving the production environment file.
7. Rebuild the API and worker, then verify health, dashboard access, database connectivity,
   Telegram polling configuration, and a complete `vps.health` job.
8. Add Gmail, PC-node, browser, and Nextcloud functionality in separate specifications and
   implementation phases after the structural migration is stable.

## Deployment Safety And Rollback

- Do not stop the current containers until the replacement images build successfully.
- Do not alter the Supabase schema or migrate production data during this structural change.
- Preserve the Tailscale-only port binding and the external `supabase_default` network.
- Preserve the VPS environment file outside repository replacement operations.
- Record the running image IDs and retain the prior deployable source before switching.
- If startup or smoke verification fails, restore the source at commit `4e88338`, rebuild the
  prior Compose services, and verify `vps.health` again.

## Verification Requirements

The migration is complete only when all of the following pass:

- All existing Python tests pass from the new command-center application location.
- Ruff reports no errors for application and test code.
- Both Docker Compose services build from the new paths.
- The API and worker containers remain healthy and running after deployment.
- The dashboard is reachable only through the existing private address.
- The API can submit `vps.health`, the worker executes it, and Supabase records `succeeded`.
- Existing job, approval, audit, Gmail account, PC node, document event, and integration records
  remain intact.
- No secret, OAuth token, SSH private key, Telegram token, or mail API key appears in Git.

## Out Of Scope

- New Gmail deletion behavior or OAuth onboarding.
- New PC command execution or administrative bypass mechanisms.
- New browser automation features.
- Replacing the live Nextcloud watcher.
- Installing Hermes, changing model providers, or adding OpenRouter configuration.
- Public internet exposure, multi-user access, or removal of Telegram approvals.
- Nx, distributed build caching, or a JavaScript workspace toolchain.

Each excluded capability receives its own design and implementation cycle after this migration.
