import json

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from pydantic import Field

from agent import __main__ as cli
from agent import main


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies and keeps what it was sent."""

    received: list[list[BaseMessage]] = Field(default_factory=list)

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.received.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


def calls(*tool_calls):
    """One scripted reply per tool call, each with a single call."""
    return [
        AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": str(i)}])
        for i, (name, args) in enumerate(tool_calls)
    ]


def stub(*tool_calls, reply="Done."):
    return StubModel(messages=iter([*calls(*tool_calls), AIMessage(content=reply)]))


def decision(claim_id, kind, payout):
    return (
        "record_decision",
        {
            "claim_id": claim_id,
            "decision": kind,
            "payout": payout,
            "section": "3. Trip Delay",
            "reason": "The delay is covered. Every expense has a receipt.",
        },
    )


READS = (
    ("get_claim", {"claim_id": "CLM-1001"}),
    ("get_policy", {"policy_id": "POL-2001"}),
    ("get_claim_history", {"customer_id": "CUS-3001"}),
)


def test_tools_are_the_claim_operations(api):
    names = [t.name for t in main.TOOLS]
    assert names == [
        "get_claim",
        "get_policy",
        "get_claim_history",
        "record_decision",
        "pay_claim",
    ]
    schema = api.get("/openapi.json").json()
    operations = {
        op["operationId"] for path in schema["paths"].values() for op in path.values()
    }
    assert set(names) <= operations


def test_system_prompt_is_the_instructions(api):
    llm = stub()
    main.run("CLM-1001", "thread-1", llm)
    first = llm.received[0][0]
    assert isinstance(first, SystemMessage)
    assert first.content == api.get("/api/instructions").json()["text"]


def test_run_approves_and_pays_within_the_limit(api):
    reply = "Approved for $420.00 under section 3. The delay was covered."
    llm = stub(
        *READS,
        decision("CLM-1001", "approve", 420.0),
        ("pay_claim", {"claim_id": "CLM-1001", "amount": 420.0}),
        reply=reply,
    )
    assert main.run("CLM-1001", "thread-1", llm) == reply

    claim = api.get("/api/claims/CLM-1001").json()
    assert claim["status"] == "decided"
    assert claim["thread_id"] == "thread-1"
    assert claim["decision"]["payout"] == 420.0
    assert claim["payment"]["amount"] == 420.0

    steps = api.get("/api/claims/CLM-1001/steps").json()
    tools = [
        "get_claim",
        "get_policy",
        "get_claim_history",
        "record_decision",
        "pay_claim",
    ]
    expected = [(kind, name) for name in tools for kind in ("tool_call", "tool_result")]
    assert [(s["kind"], s["content"].split()[0]) for s in steps] == [
        *expected,
        ("message", "Approved"),
    ]
    assert steps[0]["content"] == 'get_claim {"claim_id": "CLM-1001"}'
    assert "My flight home from Rome" in steps[1]["content"]
    assert steps[-1]["content"] == reply


def test_run_over_the_limit_is_held_for_sign_off(api):
    llm = stub(
        ("get_claim", {"claim_id": "CLM-1010"}),
        decision("CLM-1010", "approve", 1350.0),
        ("pay_claim", {"claim_id": "CLM-1010", "amount": 1350.0}),
    )
    assert main.run("CLM-1010", "thread-2", llm) == "Done."

    refusal = llm.received[-1][-1]
    assert isinstance(refusal, ToolMessage)
    assert refusal.name == "pay_claim"
    assert "403" in refusal.text
    assert "sign-off" in refusal.text

    claim = api.get("/api/claims/CLM-1010").json()
    assert claim["status"] == "waiting_for_sign_off"
    assert claim["payment"] is None


@pytest.mark.parametrize("kind", ["decline", "refer"])
def test_run_declines_and_refers_without_paying(api, kind):
    llm = stub(*READS, decision("CLM-1001", kind, 0))
    main.run("CLM-1001", "thread-3", llm)
    claim = api.get("/api/claims/CLM-1001").json()
    assert claim["status"] == "decided"
    assert claim["decision"]["decision"] == kind
    assert claim["payment"] is None


def test_a_refused_tool_call_reaches_the_model(api):
    llm = stub(("get_claim", {"claim_id": "CLM-9999"}))
    main.run("CLM-1001", "thread-4", llm)
    result = llm.received[-1][-1]
    assert isinstance(result, ToolMessage)
    assert result.text.startswith("Refused with status 404")
    assert (
        json.loads(result.text.split(": ", 1)[1])["detail"]
        == "No claim with id CLM-9999"
    )


def test_run_records_the_model_text_beside_its_tool_calls(api):
    thinking = AIMessage(
        content="Let me read the claim.",
        tool_calls=[{"name": "get_claim", "args": {"claim_id": "CLM-1001"}, "id": "1"}],
    )
    llm = StubModel(messages=iter([thinking, AIMessage(content="Done.")]))
    main.run("CLM-1001", "thread-5", llm)
    steps = api.get("/api/claims/CLM-1001/steps").json()
    assert [s["kind"] for s in steps] == [
        "message",
        "tool_call",
        "tool_result",
        "message",
    ]


@pytest.mark.usefixtures("api")
def test_command_line_works_one_claim_in_a_new_thread(monkeypatch, capsys):
    threads = []
    monkeypatch.setattr(
        cli, "run", lambda claim_id, thread_id: threads.append(thread_id) or "Reply."
    )
    cli.main(["CLM-1001"])
    cli.main(["CLM-1001"])
    assert capsys.readouterr().out == "Reply.\nReply.\n"
    assert threads[0] != threads[1]
    assert all(t.startswith("CLM-1001-") for t in threads)


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    assert main.model().reasoning_effort == "low"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
