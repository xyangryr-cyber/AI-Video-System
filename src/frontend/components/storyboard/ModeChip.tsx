import type { ReactElement } from "react";

export interface ModeChipProps {
  mode: "preview" | "production";
}

export function ModeChip({ mode }: ModeChipProps): ReactElement {
  const label = mode === "preview" ? "preview" : "production";
  const bg = mode === "preview" ? "#e5e7eb" : "#dbeafe";
  const fg = mode === "preview" ? "#374151" : "#1e40af";

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        fontSize: "11px",
        fontWeight: 600,
        borderRadius: "4px",
        backgroundColor: bg,
        color: fg,
      }}
    >
      {label}
    </span>
  );
}
