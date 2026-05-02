import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorModal } from "@frontend/components/errors/ErrorModal";

describe("ErrorModal", () => {
  it("renders >= 2 action buttons for user_choice tier", () => {
    const onAction = vi.fn();
    render(
      <ErrorModal
        code="EVID_4001" message="产物不存在"
        actions={["regenerate", "skip_phase"]} tier="user_choice"
        onAction={onAction} onClose={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("button").length).toBeGreaterThanOrEqual(2);
  });

  it("renders expandable technical details for user_action tier", async () => {
    render(
      <ErrorModal
        code="EVID_3001" message="Agent 崩溃"
        actions={["retry_manual"]} tier="user_action"
        details={{ stack: "traceback…" }}
        onAction={vi.fn()} onClose={vi.fn()}
      />,
    );
    const toggle = screen.getByRole("button", { name: /技术详情/ });
    await userEvent.click(toggle);
    expect(screen.getByText(/traceback/)).toBeInTheDocument();
  });

  it("clicking an action calls onAction with action name", async () => {
    const onAction = vi.fn();
    render(
      <ErrorModal
        code="EVID_4001" message="x" actions={["regenerate"]} tier="user_choice"
        onAction={onAction} onClose={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /regenerate/ }));
    expect(onAction).toHaveBeenCalledWith("regenerate");
  });
});
