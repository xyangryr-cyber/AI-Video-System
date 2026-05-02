interface BlockingBadgeProps {
  count: number;
}

export function BlockingBadge({ count }: BlockingBadgeProps) {
  const severity = count > 0 ? "red" : "green";
  return (
    <span
      data-testid="blocking-badge"
      data-severity={severity}
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: "12px",
        background: severity === "red" ? "#fef2f2" : "#f0fdf4",
        color: severity === "red" ? "#dc2626" : "#16a34a",
        fontWeight: 600,
        fontSize: "0.875rem",
      }}
    >
      {count} blocking
    </span>
  );
}
