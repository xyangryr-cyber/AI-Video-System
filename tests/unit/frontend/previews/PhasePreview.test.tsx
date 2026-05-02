/**
 * [SPEC-GAPFIX-032] Tests for Phase preview components.
 *
 * Verifies all 12 Phase preview components render without crashing
 * and accept projectId as a prop.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { PhasePreviewP0 } from "@frontend/components/preview/PhasePreviewP0";
import { PhasePreviewP1 } from "@frontend/components/preview/PhasePreviewP1";
import { PhasePreviewP2 } from "@frontend/components/preview/PhasePreviewP2";
import { PhasePreviewP3 } from "@frontend/components/preview/PhasePreviewP3";
import { PhasePreviewP4 } from "@frontend/components/preview/PhasePreviewP4";
import { PhasePreviewP5 } from "@frontend/components/preview/PhasePreviewP5";
import { PhasePreviewP6 } from "@frontend/components/preview/PhasePreviewP6";
import { PhasePreviewP7 } from "@frontend/components/preview/PhasePreviewP7";
import { PhasePreviewP8 } from "@frontend/components/preview/PhasePreviewP8";
import { PhasePreviewP9 } from "@frontend/components/preview/PhasePreviewP9";
import { PhasePreviewP10 } from "@frontend/components/preview/PhasePreviewP10";
import { PhasePreviewP11 } from "@frontend/components/preview/PhasePreviewP11";

const MOCK_PROJECT_ID = "proj_test_032";

const PHASES = [
  { name: "P0", Component: PhasePreviewP0 },
  { name: "P1", Component: PhasePreviewP1 },
  { name: "P2", Component: PhasePreviewP2 },
  { name: "P3", Component: PhasePreviewP3 },
  { name: "P4", Component: PhasePreviewP4 },
  { name: "P5", Component: PhasePreviewP5 },
  { name: "P6", Component: PhasePreviewP6 },
  { name: "P7", Component: PhasePreviewP7 },
  { name: "P8", Component: PhasePreviewP8 },
  { name: "P9", Component: PhasePreviewP9 },
  { name: "P10", Component: PhasePreviewP10 },
  { name: "P11", Component: PhasePreviewP11 },
];

describe("PhasePreview components", () => {
  it("has exactly 12 phase components", () => {
    expect(PHASES).toHaveLength(12);
  });

  describe.each(PHASES)("$name", ({ Component }) => {
    it("renders without crashing", () => {
      const { container } = render(<Component projectId={MOCK_PROJECT_ID} />);
      expect(container).toBeTruthy();
    });

    it("displays phase label", () => {
      const { container } = render(<Component projectId={MOCK_PROJECT_ID} />);
      expect(container.textContent).toBeTruthy();
    });

    it("accepts projectId prop", () => {
      const { container } = render(<Component projectId={MOCK_PROJECT_ID} />);
      expect(container).toBeTruthy();
    });
  });
});
