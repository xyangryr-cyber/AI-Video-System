import type { DataPoint } from "../types/dataVerification";

interface DataPointRowProps {
  dataPoint: DataPoint;
  isExpanded: boolean;
  onToggle: () => void;
  onVerify: (id: string) => void;
  onManualConfirm: (id: string) => void;
}

export function DataPointRow({
  dataPoint,
  isExpanded,
  onToggle,
  onVerify,
  onManualConfirm,
}: DataPointRowProps) {
  const { id, value, source, trust_level, verification_status, fact_checker_notes } =
    dataPoint;
  const isRefuted = verification_status === "failed";

  return (
    <div
      data-testid={`dp-row-${id}`}
      data-status={verification_status}
      onClick={onToggle}
      style={{
        border: `1px solid ${isRefuted ? "#ef4444" : "#e5e7eb"}`,
        padding: "8px",
        margin: "4px 0",
        cursor: "pointer",
        background: isRefuted ? "#fef2f2" : "transparent",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: 600 }}>{value}</span>
        <span style={{ color: "#6b7280", fontSize: "0.875rem" }}>{source}</span>
        <span
          style={{
            padding: "2px 6px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            background:
              trust_level === "user_verified"
                ? "#dcfce7"
                : trust_level === "stale"
                  ? "#f3f4f6"
                  : "#fef9c3",
            color:
              trust_level === "user_verified"
                ? "#166534"
                : trust_level === "stale"
                  ? "#6b7280"
                  : "#854d0e",
          }}
        >
          {trust_level}
        </span>
      </div>

      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
        {trust_level === "llm_generated" && (
          <>
            <button onClick={(e) => { e.stopPropagation(); onVerify(id); }}>Verify</button>
            <button onClick={(e) => { e.stopPropagation(); onManualConfirm(id); }}>Manual Confirm</button>
          </>
        )}
        {trust_level === "stale" && (
          <button onClick={(e) => { e.stopPropagation(); onVerify(id); }}>Verify</button>
        )}
      </div>

      {isExpanded && fact_checker_notes && (
        <div style={{ marginTop: "8px", padding: "8px", background: "#f9fafb", borderRadius: "4px" }}>
          {fact_checker_notes}
        </div>
      )}
    </div>
  );
}
