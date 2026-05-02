import { useState } from "react";
import type { ReactElement } from "react";

export interface WritebackSuggestion {
  id: string;
  key: string;
  current_value: unknown;
  historical_value: unknown;
  recommended_action: "keep" | "update" | "add_stage_override";
  recommended_value: unknown;
  description: string;
}

interface Props {
  projectId: string;
  suggestions: WritebackSuggestion[];
  onSave: (selectedIds: string[]) => void;
  onDismiss: () => void;
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return "-";
  if (typeof v === "number") return String(v);
  return String(v);
}

export function PreferenceWritebackCard({
  projectId: _projectId,
  suggestions,
  onSave,
  onDismiss,
}: Props): ReactElement {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    setSelected(new Set(suggestions.map((s) => s.id)));
  };

  const save = () => {
    if (selected.size === 0) return;
    onSave(Array.from(selected));
  };

  return (
    <div className="border rounded p-4 space-y-4" data-testid="preference-writeback-card">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th scope="col" className="text-left p-2 border-b w-8">
              <span className="sr-only">Select</span>
            </th>
            <th scope="col" className="text-left p-2 border-b">
              当前设置
            </th>
            <th scope="col" className="text-left p-2 border-b">
              历史偏好
            </th>
            <th scope="col" className="text-left p-2 border-b">
              推荐操作
            </th>
          </tr>
        </thead>
        <tbody>
          {suggestions.map((s) => (
            <tr key={s.id}>
              <td className="p-2 border-b">
                <input
                  type="checkbox"
                  aria-label={`Select ${s.key}`}
                  checked={selected.has(s.id)}
                  onChange={() => toggle(s.id)}
                />
              </td>
              <td className="p-2 border-b text-sm">{formatValue(s.current_value)}</td>
              <td className="p-2 border-b text-sm">{formatValue(s.historical_value)}</td>
              <td className="p-2 border-b text-sm">
                <span className="font-medium">{s.recommended_action}</span>
                <span className="mx-1">→</span>
                <span>{formatValue(s.recommended_value)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {suggestions.map((s) => (
        <div key={`desc-${s.id}`} className="text-xs text-gray-500">
          {s.key}: {s.description}
        </div>
      ))}

      <div className="flex gap-2">
        <button
          className="px-3 py-1 border rounded text-sm"
          onClick={selectAll}
        >
          全选
        </button>
        <button
          className="px-3 py-1 border rounded text-sm bg-blue-500 text-white"
          disabled={selected.size === 0}
          onClick={save}
        >
          保存勾选项
        </button>
        <button
          className="px-3 py-1 border rounded text-sm"
          onClick={onDismiss}
        >
          忽略
        </button>
      </div>
    </div>
  );
}
