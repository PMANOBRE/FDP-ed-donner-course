"""Work one claim from the command line: uv run -m agent CLM-1001."""

import sys
from uuid import uuid4

from agent.main import run


def main(args: list[str]) -> None:
    """Work the claim named in the arguments, in a new thread, and print the reply."""
    claim_id = args[0]
    print(run(claim_id, f"{claim_id}-{uuid4().hex[:8]}"))


if __name__ == "__main__":
    main(sys.argv[1:])
