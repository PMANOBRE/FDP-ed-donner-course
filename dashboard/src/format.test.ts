import { expect, it } from "vitest";
import { date, money, words } from "./format";

it("shows money in US dollars", () => {
  expect(money(1150)).toBe("$1,150.00");
  expect(money(420.5)).toBe("$420.50");
  expect(money(0)).toBe("$0.00");
});

it("shows calendar dates without shifting the day", () => {
  expect(date("2026-06-24")).toBe("Jun 24, 2026");
});

it("shows codes as words", () => {
  expect(words("trip_delay")).toBe("Trip delay");
  expect(words("baggage")).toBe("Baggage");
});
