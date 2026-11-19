"""The UnderCover Agent, which decides claims through the backend's API."""

import json
import os
from collections.abc import Iterable, Iterator
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://localhost:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
CHECKPOINTER = InMemorySaver()


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def answer(response: httpx.Response) -> str:
    """The backend's JSON, or why it refused, for the model to read."""
    if response.is_error:
        return f"Refused with status {response.status_code}: {response.text}"
    return response.text


def get(path: str) -> str:
    """Read from the backend."""
    with backend() as client:
        return answer(client.get(path))


def post(path: str, body: dict[str, Any]) -> str:
    """Send a request to the backend."""
    with backend() as client:
        return answer(client.post(path, json=body))


@tool
def get_claim(claim_id: str) -> str:
    """Get a claim in full: the customer's story, the items and the documents."""
    return get(f"/api/claims/{claim_id}")


@tool
def get_policy(policy_id: str) -> str:
    """Get a policy: its plan, add-ons, purchase date, trip and travelers."""
    return get(f"/api/policies/{policy_id}")


@tool
def get_claim_history(customer_id: str) -> str:
    """Get a customer's earlier claims."""
    return get(f"/api/customers/{customer_id}/claims")


@tool
def record_decision(
    claim_id: str,
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    section: str,
    reason: str,
) -> str:
    """Record your decision on a claim, once.

    The payout is 0 unless you approve. The section is the policy section the
    decision relies on, and the reason is two or three sentences.
    """
    return post(
        f"/api/claims/{claim_id}/decision",
        {"decision": decision, "payout": payout, "section": section, "reason": reason},
    )


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Pay an approved claim exactly its approved payout."""
    return post(f"/api/claims/{claim_id}/payment", {"amount": amount})


TOOLS = [get_claim, get_policy, get_claim_history, record_decision, pay_claim]


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def steps(message: BaseMessage) -> list[tuple[str, str]]:
    """The steps one message adds to the record, as (kind, content) pairs."""
    if isinstance(message, ToolMessage):
        return [("tool_result", f"{message.name} {message.text}")]
    found = [("message", str(message.text))] if message.text else []
    if isinstance(message, AIMessage):
        found += [
            ("tool_call", f"{call['name']} {json.dumps(call['args'])}")
            for call in message.tool_calls
        ]
    return found


def new_messages(updates: Iterable[dict[str, Any]]) -> Iterator[BaseMessage]:
    """The messages each node of the agent adds, as they arrive."""
    for update in updates:
        for node in update.values():
            yield from node["messages"]


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Work one claim, recording each step as it happens, and return the reply."""
    with backend() as client:
        client.post(
            f"/api/claims/{claim_id}/start", json={"thread_id": thread_id}
        ).raise_for_status()
        instructions = client.get("/api/instructions").raise_for_status().json()
        agent = create_agent(
            llm or model(),
            tools=TOOLS,
            system_prompt=instructions["text"],
            checkpointer=CHECKPOINTER,
        )
        updates = agent.stream(
            {"messages": [{"role": "user", "content": f"Please decide {claim_id}."}]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
        )
        reply = ""
        for message in new_messages(updates):
            for kind, content in steps(message):
                client.post(
                    f"/api/claims/{claim_id}/steps",
                    json={"kind": kind, "content": content},
                ).raise_for_status()
            if isinstance(message, AIMessage) and message.text:
                reply = message.text
    return reply
