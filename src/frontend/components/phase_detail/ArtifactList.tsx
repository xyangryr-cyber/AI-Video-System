import type { ReactElement } from "react";
import type { ArtifactEntry } from "../PhaseDetailDrawer";

interface Props {
  artifacts: ArtifactEntry[] | null | undefined;
  readOnly: boolean;
}

export function ArtifactList({ artifacts, readOnly: _readOnly }: Props): ReactElement {
  if (!artifacts || artifacts.length === 0) {
    return (
      <div data-testid="block-artifact-list" className="p-3 border rounded text-gray-500">
        No data — no artifacts recorded for this phase.
      </div>
    );
  }
  return (
    <div data-testid="block-artifact-list" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Artifact List</h3>
      <ul className="space-y-1">
        {artifacts.map((a, i) => (
          <li key={i} className="text-sm">
            <span className="font-mono">{a.name}</span>{" "}
            <span className="text-gray-400">v{a.version}</span>
            {a.url && (
              <a href={a.url} className="ml-2 text-blue-600 underline text-xs">
                Download
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
