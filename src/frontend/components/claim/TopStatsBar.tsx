import type { ClaimRow } from "../../types/claim";
import { BlockingBadge } from "./BlockingBadge";

interface TopStatsBarProps {
  claims: ClaimRow[];
}

export function TopStatsBar({ claims }: TopStatsBarProps) {
  const total = claims.length;
  const verified = claims.filter((c) => c.verification_status === "verified").length;
  const unverified = claims.filter(
    (c) => c.verification_status === "unverified" && c.hard_blocking,
  ).length;

  return (
    <div
      data-testid="top-stats-bar"
      style={{ display: "flex", gap: "16px", alignItems: "center", padding: "8px 0" }}
    >
      <span>Total: {total}</span>
      <span>Verified: {verified}</span>
      <span>Unverified: {claims.filter((c) => c.verification_status === "unverified").length}</span>
      <BlockingBadge count={unverified} />
    </div>
  );
}
