"""Work claims from the command line.

uv run -m agent CLM-1001 works one claim; uv run -m agent works every waiting claim.
"""

import sys

from agent import main as agent


def main(args: list[str]) -> None:
    """Work the claim named in the arguments, or else the whole queue."""
    if args:
        claim_id = args[0]
        print(agent.run(claim_id, agent.new_thread_id(claim_id)))
    else:
        agent.work_queue()


if __name__ == "__main__":
    main(sys.argv[1:])
