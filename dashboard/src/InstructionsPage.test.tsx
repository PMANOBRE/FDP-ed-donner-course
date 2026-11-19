import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InstructionsPage } from "./InstructionsPage";
import { stubFetch } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const text = `# The UnderCover Agent

Decide from the policy wording.

# Policy Wording

| Benefit | Economy |
|---|---|
| Deductible | $100 |`;

it("shows the instructions and the policy wording, read only", async () => {
  stubFetch({ "/api/instructions": { text } });
  render(<InstructionsPage />);
  expect(
    await screen.findByRole("heading", { name: "The UnderCover Agent" }),
  ).toBeDefined();
  expect(screen.getByRole("heading", { name: "Policy Wording" })).toBeDefined();
  expect(screen.getByRole("cell", { name: "Deductible" })).toBeDefined();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
});
