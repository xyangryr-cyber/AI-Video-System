import type { ReactElement } from "react";

interface Props {
  questions: string[];
  answers: Record<number, string>;
  onAnswerChange: (index: number, value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

const PRIORITY_KEYWORDS: Array<{ regex: RegExp; priority: number }> = [
  { regex: /time|range|date|period|granularity|frequency|interval/i, priority: 0 },
  { regex: /entity|metric|stock|symbol|index|company|instrument/i, priority: 1 },
  { regex: /unit|currency|measure|scale/i, priority: 2 },
];

function getPriority(question: string): number {
  for (const entry of PRIORITY_KEYWORDS) {
    if (entry.regex.test(question)) return entry.priority;
  }
  return 3;
}

export function ClarificationQuestionList({
  questions,
  answers,
  onAnswerChange,
  onSubmit,
  disabled = false,
}: Props): ReactElement {
  const prioritized = questions
    .map((q, idx) => ({ question: q, originalIndex: idx, priority: getPriority(q) }))
    .sort((a, b) => a.priority - b.priority)
    .slice(0, 2);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">澄清问题</h3>
      {prioritized.map((item) => (
        <div key={item.originalIndex} className="space-y-1">
          <label className="text-xs text-gray-600">{item.question}</label>
          <input
            type="text"
            className="w-full border rounded px-2 py-1 text-sm"
            value={answers[item.originalIndex] || ""}
            onChange={(e) => onAnswerChange(item.originalIndex, e.target.value)}
            disabled={disabled}
            aria-label={item.question}
          />
        </div>
      ))}
      {prioritized.length > 0 && (
        <button
          type="button"
          className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
          onClick={onSubmit}
          disabled={disabled}
        >
          提交澄清
        </button>
      )}
    </div>
  );
}
