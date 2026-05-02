import { useState } from "react";
import type { ReactElement } from "react";

export function TechnicalDetails({ details }: { details: unknown }): ReactElement {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        type="button"
        className="text-xs text-blue-600 underline"
        onClick={() => setOpen(!open)}
      >
        {open ? "隐藏" : "查看"} 技术详情
      </button>
      {open && (
        <pre className="mt-2 p-2 bg-gray-100 text-xs overflow-auto max-h-48">
          {JSON.stringify(details, null, 2)}
        </pre>
      )}
    </div>
  );
}
