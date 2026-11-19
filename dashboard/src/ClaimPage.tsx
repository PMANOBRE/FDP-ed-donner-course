import {
  getClaim,
  getClaimHistory,
  getPolicy,
  type Claim,
  type ClaimHistory,
  type Policy,
} from "./api";
import { StatusBadge } from "./Badges";
import { date, money, words } from "./format";
import { Pending } from "./Pending";
import { useData } from "./useData";

function Items({ claim }: Readonly<{ claim: Claim }>) {
  const total = claim.items.reduce((sum, item) => sum + item.amount, 0);
  return (
    <section className="panel">
      <h2>Items claimed</h2>
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Category</th>
            <th className="number">Amount</th>
          </tr>
        </thead>
        <tbody>
          {claim.items.map((item) => (
            <tr key={item.description}>
              <td>{item.description}</td>
              <td>{words(item.category)}</td>
              <td className="number mono">{money(item.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th colSpan={2}>Total</th>
            <td className="number mono">{money(total)}</td>
          </tr>
        </tfoot>
      </table>
    </section>
  );
}

function Documents({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <section className="panel">
      <h2>Documents</h2>
      {claim.documents.map((document) => (
        <article className="document" key={document.name}>
          <h3>
            {document.name} <span className="tag">{words(document.type)}</span>
          </h3>
          <p>{document.content}</p>
        </article>
      ))}
    </section>
  );
}

function PolicyDetails({ policy }: Readonly<{ policy: Policy }>) {
  const { trip } = policy;
  return (
    <dl className="facts">
      <dt>Policy</dt>
      <dd className="mono">{policy.policy_id}</dd>
      <dt>Plan</dt>
      <dd>{policy.plan_name}</dd>
      <dt>Add-ons</dt>
      <dd>
        {policy.add_ons.length ? policy.add_ons.map(words).join(", ") : "None"}
      </dd>
      <dt>Purchased</dt>
      <dd>{date(policy.purchased_on)}</dd>
      <dt>Trip</dt>
      <dd>
        {trip.destination}, {date(trip.departs_on)} to {date(trip.returns_on)}
      </dd>
      <dt>Trip cost</dt>
      <dd className="mono">{money(trip.trip_cost)}</dd>
      <dt>Travelers</dt>
      <dd>{policy.travelers.join(", ")}</dd>
    </dl>
  );
}

function PolicyPanel({ policyId }: Readonly<{ policyId: string }>) {
  const policy = useData(policyId, getPolicy);
  return (
    <section className="panel">
      <h2>Policy</h2>
      {policy.state === "ready" ? (
        <PolicyDetails policy={policy.data} />
      ) : (
        <Pending loaded={policy} missing="Policy not found" />
      )}
    </section>
  );
}

function EarlierClaims({ history }: Readonly<{ history: ClaimHistory }>) {
  if (!history.previous_claims.length) {
    return <p className="muted">No earlier claims.</p>;
  }
  return (
    <ul className="earlier">
      {history.previous_claims.map((claim) => (
        <li key={claim.claim_id}>
          <span className="mono">{claim.claim_id}</span>, filed{" "}
          {date(claim.filed_on)}
          <br />
          {claim.summary}
          <br />
          {words(claim.outcome)}, paid{" "}
          <span className="mono">{money(claim.amount_paid)}</span>
        </li>
      ))}
    </ul>
  );
}

function HistoryPanel({ customerId }: Readonly<{ customerId: string }>) {
  const history = useData(customerId, getClaimHistory);
  return (
    <section className="panel">
      <h2>Earlier claims</h2>
      {history.state === "ready" ? (
        <EarlierClaims history={history.data} />
      ) : (
        <Pending loaded={history} missing="Customer not found" />
      )}
    </section>
  );
}

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const loaded = useData(claimId, getClaim);
  if (loaded.state !== "ready") {
    return <Pending loaded={loaded} missing="Claim not found" />;
  }
  const claim = loaded.data;
  return (
    <>
      <div className="title">
        <h1 className="mono">{claim.claim_id}</h1>
        <StatusBadge status={claim.status} />
      </div>
      <p className="lede">
        {claim.customer_name} · {words(claim.claim_type)} · {claim.summary}
      </p>
      <div className="claim">
        <div className="claim-main">
          <section className="panel">
            <h2>Story</h2>
            <p>{claim.story}</p>
            <dl className="facts">
              <dt>Incident</dt>
              <dd>
                {date(claim.incident_date)}, {claim.incident_location}
              </dd>
              <dt>Submitted</dt>
              <dd>{date(claim.submitted_on)}</dd>
              <dt>Claimed</dt>
              <dd className="mono">{money(claim.amount_claimed)}</dd>
            </dl>
          </section>
          <Items claim={claim} />
          <Documents claim={claim} />
        </div>
        <aside className="claim-side">
          <PolicyPanel policyId={claim.policy_id} />
          <HistoryPanel customerId={claim.customer_id} />
        </aside>
      </div>
    </>
  );
}
