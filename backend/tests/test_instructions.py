from backend.main import INSTRUCTIONS
from backend.seed import DATA


def test_instructions_are_followed_by_the_policy_wording(api):
    text = api.get("/api/instructions").json()["text"]
    wording = (DATA / "policy_wording.md").read_text()
    assert text.startswith("# The UnderCover Agent")
    assert text.endswith(wording)
    assert "## 10. How we work out your payment" in text


def test_instructions_name_the_limit_from_the_settings(api):
    text = api.get("/api/instructions").json()["text"]
    assert "{limit}" in INSTRUCTIONS.read_text()
    assert "{limit}" not in text
    assert "A payout over $1,000.00 needs a handler's sign-off" in text
