import { useState } from "react";
import type { ReactElement } from "react";

export interface AlternativeOption {
  label: string;
  action: string;
}

interface Props {
  category: string;
  template_message: string;
  reason?: string;
  alternative_options?: AlternativeOption[];
  response_type: "refuse" | "restrict" | "clarify";
}

export function SafetyResponseCard({
  category,
  template_message,
  reason,
  alternative_options,
  response_type,
}: Props): ReactElement {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div
      role="alert"
      aria-live="polite"
      className="border rounded p-4 space-y-3"
      data-testid="safety-response-card"
    >
      <div className="flex items-center gap-2">
        <span
          aria-label={`Safety category: ${category}`}
          className="px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-700"
        >
          {category}
        </span>
        <span className="text-sm font-medium">Safety Response</span>
      </div>

      <p className="text-sm text-gray-800">{template_message}</p>

      {reason && (
        <div>
          <button
            className="text-xs text-blue-600 hover:underline focus:outline-none"
            onClick={() => setCollapsed((prev) => !prev)}
            aria-expanded={!collapsed}
          >
            {collapsed ? "v" : "^"} 为什么这个回复？
          </button>
          {!collapsed && (
            <div className="mt-1 text-xs text-gray-600 border-l-2 border-gray-300 pl-2">
              {reason}
            </div>
          )}
        </div>
      )}

      {response_type === "clarify" && alternative_options && alternative_options.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-1">您也可以：</p>
          <div className="flex flex-wrap gap-2">
            {alternative_options.map((opt) => (
              <button
                key={opt.action}
                className="px-2 py-1 text-xs border rounded hover:bg-gray-50"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
