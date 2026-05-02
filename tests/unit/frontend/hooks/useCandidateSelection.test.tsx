import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCandidateSelection } from "@frontend/hooks/useCandidateSelection";

const c1 = { id: "c1", is_recommended: true, preview_url: "u1" };
const c2 = { id: "c2", is_recommended: false, preview_url: "u2" };

describe("useCandidateSelection", () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); });

  it("AC-2 state transitions idle -> previewing -> selected -> confirmed", () => {
    const { result } = renderHook(() => useCandidateSelection([c1, c2], vi.fn()));
    expect(result.current.state).toBe("idle");
    act(() => result.current.preview("c1"));
    expect(result.current.state).toBe("previewing");
    act(() => result.current.select("c1"));
    expect(result.current.state).toBe("selected");
    act(() => result.current.confirm());
    expect(result.current.state).toBe("confirmed");
  });

  it("AC-3 two-step confirm: cannot confirm without select", () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useCandidateSelection([c1, c2], onConfirm));
    act(() => result.current.confirm());
    expect(onConfirm).not.toHaveBeenCalled();
    expect(result.current.state).toBe("idle");
  });

  it("AC-4 fires reminder exactly once after 60s idle", () => {
    const onReminder = vi.fn();
    renderHook(() => useCandidateSelection([c1, c2], vi.fn(), { onReminder, reminderMs: 60_000 }));
    act(() => { vi.advanceTimersByTime(59_000); });
    expect(onReminder).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(2_000); });
    expect(onReminder).toHaveBeenCalledOnce();
    act(() => { vi.advanceTimersByTime(60_000); });
    expect(onReminder).toHaveBeenCalledOnce();
  });

  it("AC-5 skipAndAccept confirms is_recommended candidate", () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useCandidateSelection([c1, c2], onConfirm));
    act(() => result.current.skipAndAccept());
    expect(onConfirm).toHaveBeenCalledWith("c1");
    expect(result.current.state).toBe("confirmed");
  });
});
