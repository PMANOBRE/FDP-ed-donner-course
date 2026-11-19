import type { Loaded } from "./useData";

/** What to show while data loads, or when it is missing or fails. */
export function Pending({
  loaded,
  missing,
}: Readonly<{
  loaded: Loaded<unknown>;
  missing: string;
}>) {
  if (loaded.state === "missing") {
    return (
      <div className="panel notice">
        <h1>{missing}</h1>
        <p>
          <a href="#/">Back to the queue</a>
        </p>
      </div>
    );
  }
  if (loaded.state === "failed") {
    return (
      <p className="panel notice" role="alert">
        Could not load this page. {loaded.message}
      </p>
    );
  }
  return <p className="muted">Loading…</p>;
}
