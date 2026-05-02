import { useDataVerification } from "../hooks/useDataVerification";
import { DataPointRow } from "./DataPointRow";
import type { DataPoint } from "../types/dataVerification";

interface DataVerificationPanelProps {
  dataPoints: DataPoint[];
}

export function DataVerificationPanel({ dataPoints: initialData }: DataVerificationPanelProps) {
  const { dataPoints, stats, expandedId, toggleExpand, manualConfirm, triggerVerify } =
    useDataVerification(initialData);

  return (
    <div data-testid="data-verification-panel">
      <div
        data-testid="stats-bar"
        style={{
          display: "flex",
          gap: "12px",
          padding: "8px",
          background: "#f3f4f6",
          borderRadius: "8px",
          marginBottom: "8px",
        }}
      >
        <span>Total: {stats.total}</span>
        <span style={{ color: "#16a34a" }}>{stats.verified} verified</span>
        <span style={{ color: "#ca8a04" }}>{stats.pending} pending</span>
        <span style={{ color: "#dc2626" }}>{stats.failed} failed</span>
        <span style={{ color: "#6b7280" }}>{stats.stale} stale</span>
      </div>

      {dataPoints.map((dp) => (
        <DataPointRow
          key={dp.id}
          dataPoint={dp}
          isExpanded={expandedId === dp.id}
          onToggle={() => toggleExpand(dp.id)}
          onVerify={triggerVerify}
          onManualConfirm={manualConfirm}
        />
      ))}
    </div>
  );
}
