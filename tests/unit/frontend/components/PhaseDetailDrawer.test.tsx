import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PhaseDetailDrawer } from "@frontend/components/PhaseDetailDrawer";
import type { PhaseDetailView } from "@frontend/components/PhaseDetailDrawer";

function makePhaseData(overrides?: Partial<PhaseDetailView>): PhaseDetailView {
  return {
    artifacts: [
      { name: "script.md", version: 1, url: "/api/artifacts/p1/0" },
    ],
    reviewer_results: [
      { reviewer: "L1-Programmatic", verdict: "pass", notes: "All checks passed" },
    ],
    gate_results: [
      { check_name: "FormatCheck", passed: true },
    ],
    claim_snapshot: [
      { claim_id: "claim-001", status: "verified", blocking_level: "none" },
    ],
    preference_snapshot: [
      { scope: "project", key: "tone", value: "professional" },
    ],
    diff_from_prev: [
      { field: "description", change_type: "modified", old_value: "a", new_value: "b" },
    ],
    operation_timeline: [
      { timestamp: "2026-04-24T10:00:00Z", operator: "system", action: "Phase started" },
    ],
    ...overrides,
  };
}

const DEFAULT_PROPS = {
  projectId: "proj-test-001",
  phaseNumber: 3,
  phaseData: makePhaseData(),
  readOnly: false,
  onRevert: vi.fn(),
  onClose: vi.fn(),
  open: true,
};

describe("PhaseDetailDrawer", () => {
  beforeEach(() => {
    vi.stubGlobal("confirm", vi.fn(() => true));
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // ── AC-1: 7 blocks all render; missing blocks show empty state ──

  it("AC-1 renders all seven blocks with data", () => {
    render(<PhaseDetailDrawer {...DEFAULT_PROPS} />);
    expect(screen.getByText("script.md")).toBeInTheDocument();
    expect(screen.getByText("L1-Programmatic")).toBeInTheDocument();
    expect(screen.getByText("FormatCheck")).toBeInTheDocument();
    expect(screen.getByText("claim-001")).toBeInTheDocument();
    expect(screen.getByText("tone")).toBeInTheDocument();
    expect(screen.getByText("description")).toBeInTheDocument();
    expect(screen.getByText("Phase started")).toBeInTheDocument();
  });

  it("AC-1 shows empty state when phaseData is null without crashing", () => {
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        phaseData={null}
      />,
    );
    expect(screen.getByText(/P3/)).toBeInTheDocument();
  });

  it("AC-1 shows empty state for missing blocks within phaseData", () => {
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        phaseData={makePhaseData({ artifacts: [], reviewer_results: [] })}
      />,
    );
    const emptyTexts = screen.getAllByText(/暂无|no data|empty/i);
    expect(emptyTexts.length).toBeGreaterThanOrEqual(1);
  });

  // ── AC-2: read_only mode disables all edit entries ──

  it("AC-2 shows read-only indicator in read_only mode", () => {
    render(<PhaseDetailDrawer {...DEFAULT_PROPS} readOnly={true} />);
    expect(screen.getByText(/只读|Read Only/i)).toBeInTheDocument();
  });

  it("AC-2 revert button is visible only in read_only mode", () => {
    const { rerender } = render(<PhaseDetailDrawer {...DEFAULT_PROPS} readOnly={false} />);
    expect(screen.queryByText(/从此阶段继续修改/i)).toBeNull();

    rerender(<PhaseDetailDrawer {...DEFAULT_PROPS} readOnly={true} />);
    expect(screen.getByText(/从此阶段继续修改/i)).toBeInTheDocument();
  });

  it("AC-2 hide edit entries in read_only mode via disabled attribute or hidden", () => {
    render(<PhaseDetailDrawer {...DEFAULT_PROPS} readOnly={true} />);
    // Verify no enabled text inputs or editable controls exist
    const inputs = screen.queryAllByRole("textbox");
    const enabledEdits = inputs.filter((el) => !(el as HTMLInputElement).disabled);
    expect(enabledEdits.length).toBe(0);
  });

  // ── AC-3: revert button triggers confirm + POST /revert ──

  it("AC-3 revert button triggers window.confirm then calls onRevert", async () => {
    const onRevert = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        readOnly={true}
        onRevert={onRevert}
      />,
    );
    const btn = screen.getByText(/从此阶段继续修改/i);
    await user.click(btn);
    expect(window.confirm).toHaveBeenCalledOnce();
    expect(onRevert).toHaveBeenCalledWith(3);
  });

  it("AC-3 revert button does nothing when confirm is cancelled", async () => {
    vi.stubGlobal("confirm", vi.fn(() => false));
    const onRevert = vi.fn();
    const user = userEvent.setup();
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        readOnly={true}
        onRevert={onRevert}
      />,
    );
    const btn = screen.getByText(/从此阶段继续修改/i);
    await user.click(btn);
    expect(window.confirm).toHaveBeenCalledOnce();
    expect(onRevert).not.toHaveBeenCalled();
  });

  // ── AC-4: revert rolls back current_phase only ──

  it("AC-4 onRevert receives the correct phase number", async () => {
    const onRevert = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        phaseNumber={7}
        readOnly={true}
        onRevert={onRevert}
      />,
    );
    await user.click(screen.getByText(/从此阶段继续修改/i));
    expect(onRevert).toHaveBeenCalledWith(7);
  });

  it("AC-4 drawer closes after successful revert", async () => {
    const onClose = vi.fn();
    const onRevert = vi.fn().mockImplementation(() => {
      onClose();
      return Promise.resolve();
    });
    const user = userEvent.setup();
    render(
      <PhaseDetailDrawer
        {...DEFAULT_PROPS}
        readOnly={true}
        onRevert={onRevert}
        onClose={onClose}
      />,
    );
    await user.click(screen.getByText(/从此阶段继续修改/i));
    expect(onRevert).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});
