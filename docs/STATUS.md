# Status

The claims pilot from `docs/PLAN.md` is being built, phase by phase.

## Built

- Phase 1: the database, the seed, the read API and the e2e servers.
- Phase 2: deciding, paying and signing off, with the $1,000 sign-off rule enforced in the payment operation.
- Phase 3: the UnderCover Agent, which decides one claim and records each step as it works.
- Phase 4: the dashboard's queue, claim and instructions pages, in the brand.
- Phase 5: the agent's steps, the decision with its payment, and the sign-off form on the claim page, all refreshing every two seconds.

## The backend

- SQLite at `undercover.db` in the repo root, or the path in `UNDERCOVER_DB`. The backend creates and seeds it on startup when it's missing. `uv run -m backend.seed` rebuilds it from `data/`.
- Reads: `health`, `get_instructions`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history`, `list_handlers` and `list_steps`.
- Writes: `start_claim`, `record_step`, `record_decision`, `pay_claim` and `sign_off_claim`. A claim goes `waiting` → `in_progress` → `decided`, or through `waiting_for_sign_off` when an approval is over the limit in `company.json`. `pay_claim` refuses such a payout with a 403 until a handler signs it off, and the sign-off pays it.

## The agent

- `run(claim_id, thread_id)` in `agent/main.py` starts the claim, takes its system prompt from `get_instructions` (`backend/instructions.md` followed by the policy wording), and streams a `create_agent` agent. It posts each tool call, tool result and message to `record_step` as it arrives.
- Its tools are `get_claim`, `get_policy`, `get_claim_history`, `record_decision` and `pay_claim`, each a thin wrapper over the backend operation of the same name. A refused request goes back to the model as the backend's error.
- `uv run -m agent CLM-1001` works one claim against the backend on port 8000 and prints the agent's reply. It uses `openai/gpt-6-luna` at low reasoning effort, or `MODEL_NAME`.

## The dashboard

- React and Vite at `http://localhost:5173`, with hash routes: the queue (`#/`), a claim (`#/claims/CLM-1001`) and the agent's instructions (`#/instructions`, read only).
- The queue and the claim page refresh every two seconds, so a page opened before the agent starts shows its steps as they arrive. A claim's page shows the decision, its payment, and a sign-off form when a payout waits for a handler.
- `dashboard/src/api.ts` is the typed client, `format.ts` the formatting helpers, and `styles.css` the brand: Instrument Sans, Instrument Serif for the tagline, JetBrains Mono for ids and amounts, light and dark mode from the system setting.

## End-to-end tests

- `e2e/`: Playwright starts its own backend on port 8001, on a fresh `e2e/undercover.db`, and its own dashboard on port 5174, so `npm run e2e` works while `npm run dev` is running.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173.
- `npm run check` runs every check.
