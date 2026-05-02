import type { ReactElement } from "react";
import type { PreferenceSnapshotEntry } from "../PhaseDetailDrawer";

interface Props {
  preferences: PreferenceSnapshotEntry[] | null | undefined;
  readOnly: boolean;
}

export function PreferenceSnapshot({ preferences, readOnly: _readOnly }: Props): ReactElement {
  if (!preferences || preferences.length === 0) {
    return (
      <div data-testid="block-preference-snapshot" className="p-3 border rounded text-gray-500">
        No data — no preference snapshot recorded.
      </div>
    );
  }
  return (
    <div data-testid="block-preference-snapshot" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Preference Snapshot</h3>
      <ul className="space-y-1">
        {preferences.map((p, i) => (
          <li key={i} className="text-sm">
            <span className="text-gray-500">{p.scope}</span>{" "}
            <span className="font-mono">{p.key}</span>{" "}
            <span>=</span>{" "}
            <span>{p.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
