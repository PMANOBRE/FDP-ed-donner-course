import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import type { Step } from "./api";
import { Steps } from "./Steps";

afterEach(cleanup);

const at = "2026-11-19T10:00:00Z";
const steps: Step[] = [
  {
    step_id: 1,
    kind: "tool_call",
    content: 'get_claim {"claim_id": "CLM-1002"}',
    created_at: at,
  },
  {
    step_id: 2,
    kind: "tool_result",
    content:
      'get_claim {"claim_id":"CLM-1002","story":"My suitcase never arrived."}',
    created_at: at,
  },
  {
    step_id: 3,
    kind: "tool_result",
    content: 'pay_claim Refused with status 403: {"detail":"Needs sign-off"}',
    created_at: at,
  },
  {
    step_id: 4,
    kind: "message",
    content:
      "Approved for $1,150.00 under section 5. The carrier's payment was taken off.",
    created_at: at,
  },
];

it("shows tool calls with the tool's name and inputs", () => {
  render(<Steps steps={steps} working={false} />);
  const call = screen.getByText("Calls", { exact: false }).closest("li");
  expect(call?.textContent).toContain("get_claim");
  expect(call?.textContent).toContain('"claim_id": "CLM-1002"');
});

it("folds tool results until they are opened", () => {
  render(<Steps steps={steps} working={false} />);
  const [result, refusal] = screen.getAllByRole("group");
  expect(result.hasAttribute("open")).toBe(false);
  fireEvent.click(within(result).getByText("Result from", { exact: false }));
  expect(result.hasAttribute("open")).toBe(true);
  expect(result.textContent).toContain('"story": "My suitcase never arrived."');
  expect(refusal.textContent).toContain("Refused with status 403");
});

it("shows the agent's messages in full", () => {
  render(<Steps steps={steps} working={false} />);
  expect(
    screen.getByText(
      "Approved for $1,150.00 under section 5. The carrier's payment was taken off.",
    ),
  ).toBeDefined();
});

it("says when the agent hasn't started", () => {
  render(<Steps steps={[]} working={false} />);
  expect(
    screen.getByText("The agent hasn't worked this claim yet."),
  ).toBeDefined();
});

it("says when the agent is starting", () => {
  render(<Steps steps={[]} working={true} />);
  expect(screen.getByText("Starting work…")).toBeDefined();
});
