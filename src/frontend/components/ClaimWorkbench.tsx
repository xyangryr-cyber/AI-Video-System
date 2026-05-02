import { useState, useCallback, useMemo } from "react";
import type { ClaimRow, ClaimFilters, FilterDimension, ViewMode } from "../types/claim";
import { ClaimFilterBar } from "./claim/ClaimFilterBar";
import { ClaimRowActions } from "./claim/ClaimRowActions";
import { TopStatsBar } from "./claim/TopStatsBar";
import { BlockingBadge } from "./claim/BlockingBadge";

interface ClaimWorkbenchProps {
  claims: ClaimRow[];
}

export function ClaimWorkbench({ claims }: ClaimWorkbenchProps) {
  const [filters, setFilters] = useState<ClaimFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>("card");

  const handleFilterChange = useCallback((dimension: FilterDimension, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (dimension === "verification_status" && (value === undefined || value === "verified" || value === "unverified" || value === "user_disputed" || value === "superseded")) {
        next.verification_status = value as ClaimFilters["verification_status"];
      }
      return next;
    });
  }, []);

  const filteredClaims = useMemo(() => {
    return claims.filter((c) => {
      if (filters.verification_status && c.verification_status !== filters.verification_status) return false;
      if (filters.claim_type && c.claim_type !== filters.claim_type) return false;
      return true;
    });
  }, [claims, filters]);

  const blockingCount = claims.filter((c) => c.hard_blocking && c.verification_status !== "verified").length;

  const handleVerify = useCallback((_id: string) => {}, []);
  const handleChallenge = useCallback((_id: string) => {}, []);
  const handleSupplement = useCallback((_id: string) => {}, []);
  const handleDismiss = useCallback((_id: string) => {}, []);

  return (
    <div data-testid="claim-workbench">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <TopStatsBar claims={claims} />
        <BlockingBadge count={blockingCount} />
      </div>
      <ClaimFilterBar filters={filters} onFilterChange={handleFilterChange} />
      <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
        <button onClick={() => setViewMode("table")} style={{ fontWeight: viewMode === "table" ? "bold" : "normal" }}>
          Table
        </button>
        <button onClick={() => setViewMode("card")} style={{ fontWeight: viewMode === "card" ? "bold" : "normal" }}>
          Card
        </button>
      </div>
      <div data-testid="claims-list">
        {filteredClaims.map((claim) => (
          <div
            key={claim.claim_id}
            data-testid={`claim-row-${claim.claim_id}`}
            data-view={viewMode}
            style={{
              border: "1px solid #e5e7eb",
              padding: "8px",
              margin: "4px 0",
              borderRadius: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{claim.entity}</strong>
              <span>{claim.value}</span>
              <span>{claim.verification_status}</span>
            </div>
            <ClaimRowActions
              claimId={claim.claim_id}
              onVerify={handleVerify}
              onChallenge={handleChallenge}
              onSupplement={handleSupplement}
              onDismiss={handleDismiss}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
