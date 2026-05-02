import type { ReactElement } from "react";

interface Props {
  verified: boolean;
  sourceLabel: string;
}

export function DataSourceBadge({ verified, sourceLabel }: Props): ReactElement {
  const label = verified ? "已验证" : "未验证";
  const className = verified
    ? "text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
    : "text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded";

  return (
    <span title={`${label}: ${sourceLabel}`} className={className}>
      {label}
    </span>
  );
}
