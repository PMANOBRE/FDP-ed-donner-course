# Status

The claims pilot from `docs/PLAN.md` is being built, phase by phase.

## Built

- Phase 1: the database, the seed, the read API and the e2e servers.
- Phase 2: deciding, paying and signing off, with the $1,000 sign-off rule enforced in the payment operation.

## The backend

- SQLite at `undercover.db` in the repo root, or the path in `UNDERCOVER_DB`. The backend creates and seeds it on startup when it's missing. `uv run -m backend.seed` rebuilds it from `data/`.
- Reads: `health`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history`, `list_handlers` and `list_steps`.
- Writes: `start_claim`, `record_step`, `record_decision`, `pay_claim` and `sign_off_claim`. A claim goes `waiting` → `in_progress` → `decided`, or through `waiting_for_sign_off` when an approval is over the limit in `company.json`. `pay_claim` refuses such a payout with a 403 until a handler signs it off, and the sign-off pays it.

## The rest

- `agent/`: still the hello-world agent, `run(claim_id, thread_id)` with one tool that calls the health route.
- `dashboard/`: still one page that shows whether the backend is up.
- `e2e/`: Playwright starts its own backend on port 8001, on a fresh `e2e/undercover.db`, and its own dashboard on port 5174, so `npm run e2e` works while `npm run dev` is running.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173.
- `npm run check` runs every check.
