import type { ReactElement } from "react";
import type { ClaimSnapshotEntry } from "../PhaseDetailDrawer";

interface Props {
  claims: ClaimSnapshotEntry[] | null | undefined;
  readOnly: boolean;
}

export function ClaimSnapshot({ claims, readOnly: _readOnly }: Props): ReactElement {
  if (!claims || claims.length === 0) {
    return (
      <div data-testid="block-claim-snapshot" className="p-3 border rounded text-gray-500">
        No data — no claim snapshot recorded.
      </div>
    );
  }
  return (
    <div data-testid="block-claim-snapshot" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Claim Snapshot</h3>
      <ul className="space-y-1">
        {claims.map((c, i) => (
          <li key={i} className="text-sm">
            <span className="font-mono text-xs">{c.claim_id}</span>{" "}
            <span className="text-gray-600">{c.status}</span>{" "}
            <span className="text-gray-400">[{c.blocking_level}]</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
