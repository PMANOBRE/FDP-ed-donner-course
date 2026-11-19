import type { Step } from "./api";
import { time } from "./format";

/** A tool step's content is the tool's name, a space, then its JSON. */
function split(content: string): [string, string] {
  const space = content.indexOf(" ");
  if (space === -1) return [content, ""];
  return [content.slice(0, space), content.slice(space + 1)];
}

function pretty(text: string) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

function StepBody({ step }: Readonly<{ step: Step }>) {
  if (step.kind === "message") {
    return (
      <>
        <span className="step-label">The agent says</span>
        <p className="step-message">{step.content}</p>
      </>
    );
  }
  const [tool, payload] = split(step.content);
  if (step.kind === "tool_call") {
    return (
      <>
        <span className="step-label">
          Calls <code className="mono">{tool}</code>
        </span>
        <pre className="mono">{pretty(payload)}</pre>
      </>
    );
  }
  return (
    <details>
      <summary>
        Result from <code className="mono">{tool}</code>
      </summary>
      <pre className="mono">{pretty(payload)}</pre>
    </details>
  );
}

export function Steps({
  steps,
  working,
}: Readonly<{ steps: Step[]; working: boolean }>) {
  return (
    <section className="panel">
      <h2>The agent&apos;s work</h2>
      {steps.length === 0 ? (
        <p className="muted">
          {working
            ? "Starting work…"
            : "The agent hasn't worked this claim yet."}
        </p>
      ) : (
        <ol className="steps">
          {steps.map((step) => (
            <li className={`step step-${step.kind}`} key={step.step_id}>
              <time className="step-time mono" dateTime={step.created_at}>
                {time(step.created_at)}
              </time>
              <StepBody step={step} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
