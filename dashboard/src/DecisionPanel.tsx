import { useState, type SyntheticEvent } from "react";
import { listHandlers, signOff, type Claim, type Decision } from "./api";
import { DecisionBadge } from "./Badges";
import { money, when } from "./format";
import { useData } from "./useData";

function SignOffForm({
  claimId,
  onSignedOff,
}: Readonly<{ claimId: string; onSignedOff: () => void }>) {
  const handlers = useData("handlers", listHandlers);
  const [handlerId, setHandlerId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    signOff(claimId, handlerId).then(onSignedOff, (reason: unknown) => {
      setError(reason instanceof Error ? reason.message : String(reason));
      setBusy(false);
    });
  };

  const eligible =
    handlers.state === "ready"
      ? handlers.data.filter((handler) => handler.can_approve_over_limit)
      : [];

  return (
    <form className="sign-off" onSubmit={submit}>
      <p>The payment is held until a handler signs it off.</p>
      <div className="sign-off-row">
        <label htmlFor="sign-off-handler">Handler</label>
        <select
          id="sign-off-handler"
          value={handlerId}
          onChange={(event) => {
            setHandlerId(event.target.value);
          }}
        >
          <option value="">Choose a handler</option>
          {eligible.map((handler) => (
            <option key={handler.handler_id} value={handler.handler_id}>
              {handler.name}
            </option>
          ))}
        </select>
        <button type="submit" disabled={!handlerId || busy}>
          Sign off
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

function Payment({
  claim,
  decision,
  onSignedOff,
}: Readonly<{ claim: Claim; decision: Decision; onSignedOff: () => void }>) {
  if (claim.payment) {
    const signedOff = claim.sign_off
      ? `, signed off by ${claim.sign_off.handler_name}`
      : "";
    return (
      <p className="payment paid">
        Paid {money(claim.payment.amount)}
        {signedOff}
      </p>
    );
  }
  if (claim.status === "waiting_for_sign_off") {
    return <SignOffForm claimId={claim.claim_id} onSignedOff={onSignedOff} />;
  }
  if (decision.decision === "approve") {
    return <p className="payment">Approved, not paid yet.</p>;
  }
  return <p className="payment muted">No payment.</p>;
}

export function DecisionPanel({
  claim,
  onSignedOff,
}: Readonly<{ claim: Claim; onSignedOff: () => void }>) {
  const { decision } = claim;
  if (!decision) {
    return (
      <section className="panel">
        <h2>Decision</h2>
        <p className="muted">
          {claim.status === "in_progress"
            ? "The agent is working on this claim."
            : "Not decided yet."}
        </p>
      </section>
    );
  }
  return (
    <section className="panel">
      <h2>Decision</h2>
      <div className="decision-head">
        <DecisionBadge decision={decision.decision} />
        <span className="payout mono">{money(decision.payout)}</span>
      </div>
      <p className="reason">{decision.reason}</p>
      <dl className="facts">
        <dt>Section</dt>
        <dd>{decision.section}</dd>
        <dt>Decided</dt>
        <dd>{when(decision.decided_at)}</dd>
      </dl>
      <Payment claim={claim} decision={decision} onSignedOff={onSignedOff} />
    </section>
  );
}
