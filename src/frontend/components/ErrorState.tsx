import type { ReactElement } from "react";

interface Props {
  message: string;
  onRetry: () => void;
}
export function ErrorState({ message, onRetry }: Props): ReactElement {
  return (
    <div data-testid="error-state" className="p-6 space-y-2">
      <div className="text-red-600">加载失败: {message}</div>
      <button className="px-3 py-1 border rounded" onClick={onRetry}>
        重试
      </button>
    </div>
  );
}
