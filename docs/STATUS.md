# Status

The claims pilot from `docs/PLAN.md` is being built, phase by phase.

## Built

- Phase 1: the database, the seed, the read API and the e2e servers.

## The backend

- SQLite at `undercover.db` in the repo root, or the path in `UNDERCOVER_DB`. The backend creates and seeds it on startup when it's missing. `uv run -m backend.seed` rebuilds it from `data/`.
- Routes: `GET /api/health`, `GET /api/claims`, `GET /api/claims/{claim_id}`, `GET /api/policies/{policy_id}` and `GET /api/customers/{customer_id}/claims`.

## The rest

- `agent/`: still the hello-world agent, `run(claim_id, thread_id)` with one tool that calls the health route.
- `dashboard/`: still one page that shows whether the backend is up.
- `e2e/`: Playwright starts its own backend on port 8001, on a fresh `e2e/undercover.db`, and its own dashboard on port 5174, so `npm run e2e` works while `npm run dev` is running.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173.
- `npm run check` runs every check.
