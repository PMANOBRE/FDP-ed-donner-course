import { listClaims, type ClaimSummary } from "./api";
import { DecisionBadge, StatusBadge } from "./Badges";
import { STATUS_LABELS, STATUSES, date, money, words } from "./format";
import { Pending } from "./Pending";
import { useData } from "./useData";

function Counts({ claims }: Readonly<{ claims: ClaimSummary[] }>) {
  return (
    <section className="counts" aria-label="Claims by state">
      {STATUSES.map((status) => (
        <div className="panel count" key={status}>
          <span className="count-number mono">
            {claims.filter((claim) => claim.status === status).length}
          </span>
          <span className={`badge status-${status}`}>
            {STATUS_LABELS[status]}
          </span>
        </div>
      ))}
    </section>
  );
}

export function QueuePage() {
  const claims = useData("queue", listClaims, true);
  if (claims.state !== "ready") {
    return <Pending loaded={claims} missing="Queue not found" />;
  }
  return (
    <>
      <h1>Claims queue</h1>
      <Counts claims={claims.data} />
      <section className="panel table-panel">
        <table>
          <thead>
            <tr>
              <th>Claim</th>
              <th>Customer</th>
              <th>Type</th>
              <th>Summary</th>
              <th className="number">Claimed</th>
              <th>Submitted</th>
              <th>Status</th>
              <th>Decision</th>
              <th className="number">Payout</th>
            </tr>
          </thead>
          <tbody>
            {claims.data.map((claim) => (
              <tr key={claim.claim_id}>
                <td className="nowrap">
                  <a className="mono" href={`#/claims/${claim.claim_id}`}>
                    {claim.claim_id}
                  </a>
                </td>
                <td>{claim.customer_name}</td>
                <td>{words(claim.claim_type)}</td>
                <td className="summary">{claim.summary}</td>
                <td className="number mono">{money(claim.amount_claimed)}</td>
                <td className="nowrap">{date(claim.submitted_on)}</td>
                <td>
                  <StatusBadge status={claim.status} />
                </td>
                <td>
                  {claim.decision && (
                    <DecisionBadge decision={claim.decision} />
                  )}
                </td>
                <td className="number mono">
                  {claim.payout === null ? "" : money(claim.payout)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
