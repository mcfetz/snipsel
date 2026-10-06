# snipsel — Development Guidelines

## Project
- Self-hosted, AI-powered notes & tasks PWA: frontend Svelte 5 / Vite / TypeScript in `frontend/`, API Flask / SQLAlchemy / uv in `backend/`.
- Two remotes — **always push to both**: `origin` (git.familie-heise.de) and `github` (github.com/mcfetz/snipsel).
- Commits use the Conventional Commits style and are always in English. No code comments unless explicitly requested.
- User-facing communication is in German.

## Project analysis
Before any significant change, run `mcp jcodemunch analyze --project-path .` to inspect codebase, structure, dependencies, and affected modules. Base changes on the discovered structure instead of assumptions.

## Quality assurance (mandatory before any work item is closed)
Repository root (config `.ruff.toml`):
- `uvx --from ruff==0.16.10 ruff check .` → 0 findings
- `uvx --from ruff==0.16.10 ruff format --check .` → 0 changes needed

`backend/` (one-time `uv sync --frozen`; config `backend/ty.toml`):
- `uvx --from ty==0.0.84 ty check .` → 0 errors

`frontend/`:
- `npm run build` → green (incl. PWA/Workbox)
- `npm run check` → svelte-check baseline: **306 pre-existing errors, add none** (there is no `npm run lint` script)

## Enforced gates
- `.pre-commit-config.yaml`: local hooks `backend-ruff` (ruff check + format) and `backend-ty` (ty, with `uv sync --frozen`) run before each commit. Requires a one-time `uv tool install pre-commit` + `pre-commit install`.
- Frontend has no pre-commit hook (no lint script); it is validated manually via `npm run build` / `npm run check` and on every push by the Docker image build (`.github/workflows/docker-publish.yml` includes the production frontend build).
- `.github/workflows/lint.yml`: jobs `ruff` (check + format) and `ty` on every push/PR to `main`.
- Version pinning: `ruff==0.16.10` and `ty==0.0.84` appear via `uvx --from` in CI, `.pre-commit-config.yaml`, and this file — **keep all three in sync when bumping**. Pin GitHub Action refs exactly (e.g. `astral-sh/setup-uv@v10.2.0`, there is no rolling `v10` tag).
- Merge Dependabot minor/patch PRs; review major bumps critically (wait if peer lint compatibility is limited).

## Standard workflow
1. Analyze the affected area with `mcp jcodemunch`.
2. Implement the requested change.
3. Run the Quality assurance commands for the affected areas (pre-commit runs the backend hooks automatically on commit).
4. Commit (English, Conventional Commits; one commit per logical unit of work).
5. Push to **both** remotes — never leave finished work only in the local working tree.
6. Send the completion notification via ntfy.

## Completion notification via ntfy

### When
- **Whenever a work item is finished**: changes validated (lint/build/tests) AND pushed to all remotes. Never before the push, never for merely planned/stopped local work.
- **One notification per work item**, not per commit (multiple commits → one summary with all SHAs).
- No notifications for: intermediate states, purely informational replies, questions, unverified work.
- Optional (recommended): a short error notification when work had to be blocked or aborted (What? Why? What is left open?).

### What to include
- Short title: `snipsel: <topic> <status>` (e.g. `snipsel: ruff/ty clean + CI lint active`).
- Message: 2–4 sentences in the language the user is writing in:
  1. what was done (the key points, no file list),
  2. last commit SHA(s) + that everything was pushed to all remotes,
  3. verification result (e.g. "Lint green, Docker build green"),
  4. open risks/warnings (e.g. failing side runs, security alerts).
- No secrets, no long logs, no markdown needed (ntfy renders plain text).

### How (in opencode)
- Call the tool `ntfy_ntfy_me` with `title` + `message`; server/topic come from the environment variables `NTFY_URL`/`NTFY_TOPIC`. If a token is needed use `NTFY_TOKEN`/accessToken, **never hardcode it**.
- Without a dedicated tool (curl):
  `curl -d "message" -H "Title: snipsel: ..." "$NTFY_URL/$NTFY_TOPIC"`

### Reference example
Title: `snipsel: Settings/API-Keys repariert, CI grün`
Message: `Settings-Bug gefixt: SettingsSecurity nutzte alte api-Struktur – neue API-Keys werden angezeigt/löschbar, Passkeys/Passcode/2FA funktionieren wieder. Dependabot-PRs #67/#68 integriert. Lint+Docker grün, 4ce423c auf beide Remotes, Security-Alerts 9→1.`

## Non-negotiables
- Do not skip `mcp jcodemunch` before substantial work.
- Do not skip validation after code changes.
- Do not leave finished work uncommitted or unpushed — and always push to both remotes.
- Do not write commit messages in any language other than English.
- Do not send the final completion update without ntfy.

## Replication template (take it to other repos)
To set up the same QA baseline in another repository, run the following there:

1. **Backend (Python/uv):** `uv add --dev ruff ty`; add `[tool.ruff]` with a matching `target-version`, `extend-exclude` only for generated folders (e.g. `alembic/versions`) with a justification comment; fix all findings down to 0 (broad excepts only with `# noqa` + justification).
2. **CI:** `.github/workflows/lint.yml` — triggers push+PR on main; job `backend`: `actions/checkout@v7`, `astral-sh/setup-uv@v10.2.0`, `uv sync --frozen --group dev`, then `uv run ruff check .` / `ruff format --check .` / `ty check .`. Optional second job `frontend`: `actions/setup-node@v7` (node 22, `cache: npm`), `npm ci`, `npm run lint`, `npm run build`.
3. **Pre-commit:** `.pre-commit-config.yaml` in the repo root — local hooks with `entry: bash -c 'cd backend && uv run …'`, `language: system`, `pass_filenames: false`, scope on `^backend/.*\.py$`.
4. **Husky (if frontend):** `npm add -D husky`, hook `.husky/pre-commit` in the git root (not in the package folder!) with a `git diff --cached --name-only | grep -q '^frontend/'` gate → `cd frontend && npm run lint && npm run build`; `"prepare": "cd .. && husky"`.
5. **Branch protection:** `gh api --method PUT repos/<owner>/<repo>/branches/main/protection` with `required_status_checks: { strict: false, contexts: ["backend","frontend"] }` (job names of the lint workflow), `enforce_admins: false`.
6. **Completion criteria:** all checks = 0/green, CI run on GitHub green, hooks run locally, both remotes pushed.
