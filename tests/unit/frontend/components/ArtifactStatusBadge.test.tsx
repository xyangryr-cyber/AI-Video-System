import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ArtifactStatusBadge } from "@frontend/components/ArtifactStatusBadge";
import { PhaseNavigation } from "@frontend/components/PhaseNavigation";

describe("ArtifactStatusBadge", () => {
  it("AC-1 renders nothing for status=ok", () => {
    const { container } = render(<ArtifactStatusBadge status="ok" />);
    expect(container.firstChild).toBeNull();
  });

  it("AC-2 renders red badge with 'damaged' label for status=damaged", () => {
    render(<ArtifactStatusBadge status="damaged" />);
    const el = screen.getByText(/damaged/i);
    expect(el).toBeInTheDocument();
    expect(el.className).toMatch(/red|danger/i);
  });

  it("AC-3 renders red badge with 'missing' label for status=missing", () => {
    render(<ArtifactStatusBadge status="missing" />);
    const el = screen.getByText(/missing/i);
    expect(el).toBeInTheDocument();
    expect(el.className).toMatch(/red|danger/i);
  });
});

describe("Badge integration via PhaseNavigation", () => {
  it("AC-4 phase button renders P0 label for phase 0", () => {
    render(
      <PhaseNavigation
        currentPhase={0}
        phases={[{ phase: 0, artifact_status: "ok" }, { phase: 1, artifact_status: "damaged" }]}
        onSelectPhase={() => {}}
        completedPhases={0}
      />,
    );
    expect(screen.getByText("P0")).toBeInTheDocument();
    expect(screen.getByText("P1")).toBeInTheDocument();
  });

  it("AC-5 phase button reflects active state when currentPhase matches", () => {
    const { rerender } = render(
      <PhaseNavigation
        currentPhase={0}
        phases={[{ phase: 0, artifact_status: "ok" }]}
        onSelectPhase={() => {}}
        completedPhases={0}
      />,
    );
    expect(screen.getByTestId("phase-nav-0")).toHaveAttribute("data-active", "true");
    rerender(
      <PhaseNavigation
        currentPhase={1}
        phases={[{ phase: 0, artifact_status: "ok" }, { phase: 1, artifact_status: "damaged" }]}
        onSelectPhase={() => {}}
        completedPhases={1}
      />,
    );
    expect(screen.getByTestId("phase-nav-0")).toHaveAttribute("data-active", "false");
    expect(screen.getByTestId("phase-nav-1")).toHaveAttribute("data-active", "true");
  });
});
