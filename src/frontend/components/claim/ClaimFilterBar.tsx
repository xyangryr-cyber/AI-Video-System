import type { ClaimFilters, FilterDimension, ClaimVerificationStatus } from "../../types/claim";

interface ClaimFilterBarProps {
  filters: ClaimFilters;
  onFilterChange: (dimension: FilterDimension, value: string | undefined) => void;
}

const STATUS_OPTIONS: ClaimVerificationStatus[] = ["verified", "unverified", "user_disputed", "superseded"];

export function ClaimFilterBar({ filters, onFilterChange }: ClaimFilterBarProps) {
  return (
    <div data-testid="claim-filter-bar" style={{ display: "flex", gap: "8px", flexWrap: "wrap", padding: "8px 0" }}>
      <button
        data-testid="filter-unverified"
        onClick={() =>
          onFilterChange("verification_status", filters.verification_status === "unverified" ? undefined : "unverified")
        }
        style={{ fontWeight: filters.verification_status === "unverified" ? "bold" : "normal" }}
      >
        unverified
      </button>
      {STATUS_OPTIONS.filter((s) => s !== "unverified").map((status) => (
        <button
          key={status}
          data-testid={`filter-${status}`}
          onClick={() =>
            onFilterChange("verification_status", filters.verification_status === status ? undefined : status)
          }
          style={{ fontWeight: filters.verification_status === status ? "bold" : "normal" }}
        >
          {status}
        </button>
      ))}
    </div>
  );
}
