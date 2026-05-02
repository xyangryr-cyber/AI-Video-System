import type { ReactElement } from "react";
import type { TimelineEvent } from "../PhaseDetailDrawer";

interface Props {
  events: TimelineEvent[] | null | undefined;
  readOnly: boolean;
}

export function OperationHistoryTimeline({ events, readOnly: _readOnly }: Props): ReactElement {
  if (!events || events.length === 0) {
    return (
      <div data-testid="block-operation-history" className="p-3 border rounded text-gray-500">
        No data — no operation history recorded.
      </div>
    );
  }
  return (
    <div data-testid="block-operation-history" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Operation History Timeline</h3>
      <ul className="space-y-1">
        {events.map((e, i) => (
          <li key={i} className="text-sm flex gap-2">
            <span className="text-gray-400 text-xs w-36 shrink-0">{e.timestamp}</span>
            <span className="font-medium">{e.operator}</span>
            <span>{e.action}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
