import type { ReactElement } from "react";
import type { DiffEntry } from "../PhaseDetailDrawer";

interface Props {
  diffs: DiffEntry[] | null | undefined;
  readOnly: boolean;
}

export function DiffView({ diffs, readOnly: _readOnly }: Props): ReactElement {
  if (!diffs || diffs.length === 0) {
    return (
      <div data-testid="block-diff-view" className="p-3 border rounded text-gray-500">
        No data — no diff from previous phase.
      </div>
    );
  }
  return (
    <div data-testid="block-diff-view" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Diff View</h3>
      <ul className="space-y-1">
        {diffs.map((d, i) => (
          <li key={i} className="text-sm">
            <span
              className={
                d.change_type === "added"
                  ? "text-green-600"
                  : d.change_type === "removed"
                    ? "text-red-600"
                    : "text-yellow-600"
              }
            >
              [{d.change_type}]
            </span>{" "}
            <span className="font-mono">{d.field}</span>
            {d.old_value && <span className="ml-1 line-through text-red-400">{d.old_value}</span>}
            {d.new_value && <span className="ml-1 text-green-600">{d.new_value}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
