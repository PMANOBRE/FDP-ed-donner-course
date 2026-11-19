import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { claim, claimRoutes, stubFetch, summary } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function stubAll() {
  stubFetch({
    "/api/claims": [summary],
    "/api/instructions": { text: "# The UnderCover Agent" },
    ...claimRoutes(claim),
  });
}

it("shows the queue by default", async () => {
  stubAll();
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Claims queue" }),
  ).toBeDefined();
  expect(
    screen.getByRole("link", { name: "Queue" }).getAttribute("aria-current"),
  ).toBe("page");
});

it("opens a claim from its route", async () => {
  stubAll();
  window.location.hash = "#/claims/CLM-1002";
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "CLM-1002" }),
  ).toBeDefined();
});

it("follows the hash as it changes", async () => {
  stubAll();
  render(<App />);
  await screen.findByRole("heading", { name: "Claims queue" });
  act(() => {
    window.location.hash = "#/instructions";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
  expect(
    await screen.findByRole("heading", { name: "The UnderCover Agent" }),
  ).toBeDefined();
  expect(
    screen
      .getByRole("link", { name: "Instructions" })
      .getAttribute("aria-current"),
  ).toBe("page");
});

it("links the header to the queue and the instructions", () => {
  stubAll();
  render(<App />);
  expect(screen.getByRole("link", { name: "Queue" }).getAttribute("href")).toBe(
    "#/",
  );
  expect(
    screen.getByRole("link", { name: "Instructions" }).getAttribute("href"),
  ).toBe("#/instructions");
});
