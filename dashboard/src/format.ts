import type { DecisionKind, Status } from "./api";

const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});
const day = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeZone: "UTC",
});
const clock = new Intl.DateTimeFormat("en-US", { timeStyle: "medium" });

/** An amount in US dollars, such as $1,250.00. */
export const money = (amount: number) => dollars.format(amount);

/** A calendar date such as 2026-06-24, as Jun 24, 2026. */
export const date = (iso: string) => day.format(new Date(iso));

/** The local time of a timestamp. */
export const time = (iso: string) => clock.format(new Date(iso));

/** A code such as trip_delay, as Trip delay. */
export const words = (code: string) =>
  code.charAt(0).toUpperCase() + code.slice(1).replaceAll("_", " ");

export const STATUSES: Status[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "decided",
];

export const STATUS_LABELS: Record<Status, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  decided: "Decided",
};

export const DECISION_LABELS: Record<DecisionKind, string> = {
  approve: "Approved",
  decline: "Declined",
  refer: "Referred",
};
