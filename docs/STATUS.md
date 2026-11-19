# Status

The claims pilot from `docs/PLAN.md` is built: a backend that holds the claims and enforces the sign-off rule, the UnderCover Agent that decides claims through the backend's API, and a dashboard where handlers watch the queue, follow the agent as it works and sign off large payouts.

## Running it

- `uv sync` and `npm install` install everything.
- `npm run dev` starts the backend on port 8000 and the dashboard on `http://localhost:5173`. The backend creates and seeds `undercover.db` on startup if it's missing.
- `uv run -m backend.seed` rebuilds the database from `data/`, putting every claim back in the queue.
- With `npm run dev` running, `uv run -m agent CLM-1001` works one claim and prints the agent's reply, and `uv run -m agent` works every waiting claim in queue order. It prints one line per claim, like `CLM-1001  approve  $420.00`, then a count of each decision. A claim that fails is reported and the queue carries on. The failed claim stays in progress, and `uv run -m agent <claim id>` works it again.
- The agent uses `openai/gpt-6-luna` at low reasoning effort through OpenRouter, with `OPENROUTER_API_KEY` from `.env`, or the model in `MODEL_NAME`, such as `openrouter/free`. OpenRouter allows new accounts and free models 20 requests a minute, so the model client backs off and retries for up to a minute when it hits the limit, and a queue run takes several minutes.
- `npm run check` runs every check.

## The backend

- FastAPI and SQLite at `undercover.db` in the repo root, or the path in `UNDERCOVER_DB`. The seed reads the company settings, plans, policies, customers, handlers, claims and policy wording from `data/`, and nothing else.
- Reads: `health`, `get_instructions`, `list_claims`, `get_claim`, `get_policy`, `get_claim_history`, `list_handlers` and `list_steps`.
- Writes: `start_claim`, `record_step`, `record_decision`, `pay_claim` and `sign_off_claim`.
- A claim goes `waiting` → `in_progress` → `decided`, or through `waiting_for_sign_off` when an approval is over the limit in `company.json` ($1,000.00). `pay_claim` refuses such a payout with a 403 until a handler signs it off, and the sign-off pays it.

## The agent

- `run(claim_id, thread_id)` in `agent/main.py` starts the claim, takes its system prompt from `get_instructions` (`backend/instructions.md` followed by the policy wording), and streams a `create_agent` agent. It posts each tool call, tool result and message to `record_step` as it arrives.
- Its tools are `get_claim`, `get_policy`, `get_claim_history`, `record_decision` and `pay_claim`, each a thin wrapper over the backend operation of the same name. A refused request goes back to the model as the backend's error, so the run carries on.

## The dashboard

- React and Vite, with hash routes: the queue (`#/`) with counts by state, a claim (`#/claims/CLM-1001`) and the agent's instructions (`#/instructions`, read only).
- A claim's page shows the story, items, documents, policy and earlier claims, the decision with its section, reason and payment, the agent's steps, and a sign-off form when a payout waits for a handler.
- The queue and the claim page refresh every two seconds, so a page opened before the agent starts shows its work as it happens.
- `dashboard/src/api.ts` is the typed client, `format.ts` the formatting helpers, and `styles.css` the brand, in light and dark mode from the system setting.

## End-to-end tests

- Playwright starts its own backend on port 8001, on a fresh `e2e/undercover.db`, and its own dashboard on port 5174, so `npm run e2e` works while `npm run dev` is running. The tests stand in for the agent by calling the API.

## The live run

On November 19, 2026, `uv run -m agent` worked all 25 claims on a fresh database in about five minutes, on `openai/gpt-6-luna`:

- 16 approved, 6 declined and 3 referred.
- 12 approvals were within the limit and paid exactly their payout. The 4 over $1,000.00 (CLM-1003, CLM-1008, CLM-1011 and CLM-1021) waited for a handler's sign-off with no payment.
- Every decision has a policy section and a reason of two sentences.

These decisions haven't been scored against the handlers' decisions in `data/evals/` yet.

## Not built yet

- Scoring the agent against the handlers' decisions in `data/evals/`.
- The claims manual, sign-in, real payments and messages to customers, which `docs/SPEC.md` leaves out of the pilot.
