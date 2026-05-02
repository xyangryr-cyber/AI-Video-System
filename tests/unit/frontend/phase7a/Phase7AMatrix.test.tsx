import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Phase7AMatrix } from "@frontend/components/phase7a/Phase7AMatrix";
import type { ShotBinding } from "@frontend/types/shot_material_binding";

interface MaterialEntry {
  material_id: string;
  material_type: string;
  verification_status: "pending" | "verified" | "rejected" | "missing";
  shot_id: string;
}

const shots: ShotBinding[] = [
  { shot_id: "shot_1", required_materials: ["mat_1", "mat_2"], optional_materials: [] },
  { shot_id: "shot_2", required_materials: ["mat_3"], optional_materials: [] },
];

const materials: MaterialEntry[] = [
  { material_id: "mat_1", material_type: "chart", verification_status: "verified", shot_id: "shot_1" },
  { material_id: "mat_2", material_type: "data", verification_status: "missing", shot_id: "shot_1" },
  { material_id: "mat_3", material_type: "chart", verification_status: "rejected", shot_id: "shot_2" },
];

const tid = (shot: string, mat: string) => `cell-${shot}-${mat}`;

describe("Phase7AMatrix", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: renders grid with status colors", () => {
    it("renders grid container with role grid", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      expect(screen.getByRole("grid")).toBeInTheDocument();
    });

    it("renders grid cells with role gridcell", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const cells = screen.getAllByRole("gridcell");
      // 2 shots x 3 material columns = 6 cells, but only cells with in-shot materials have gridcell role
      expect(cells.length).toBeGreaterThanOrEqual(3);
    });

    it("renders verified cell with data-status verified", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const verifiedCell = screen.getByTestId(tid("shot_1", "mat_1"));
      expect(verifiedCell).toHaveAttribute("data-status", "verified");
    });

    it("renders missing cell with data-status missing", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const missingCell = screen.getByTestId(tid("shot_1", "mat_2"));
      expect(missingCell).toHaveAttribute("data-status", "missing");
    });

    it("renders rejected cell with data-status rejected", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const rejectedCell = screen.getByTestId(tid("shot_2", "mat_3"));
      expect(rejectedCell).toHaveAttribute("data-status", "rejected");
    });
  });

  describe("AC-2: missing cell opens detail and refetch", () => {
    it("calls onRequestRefetch when missing cell is clicked", () => {
      const onRefetch = vi.fn();
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={onRefetch}
          onRequestChange={vi.fn()}
        />,
      );
      const missingCell = screen.getByTestId(tid("shot_1", "mat_2"));
      fireEvent.click(missingCell);
      expect(onRefetch).toHaveBeenCalledWith("mat_2");
    });
  });

  describe("AC-5: a11y grid role and cell aria", () => {
    it("grid cells have aria-label with status", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const cell = screen.getByTestId(tid("shot_1", "mat_1"));
      expect(cell).toHaveAttribute("aria-label", "已验证");
    });

    it("missing cell has aria-label 缺失", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{}}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      const cell = screen.getByTestId(tid("shot_1", "mat_2"));
      expect(cell).toHaveAttribute("aria-label", "缺失");
    });
  });

  describe("AC-6: shows anchor_text per shot row", () => {
    it("renders anchor_text when provided", () => {
      render(
        <Phase7AMatrix
          shots={shots}
          materials={materials}
          anchorTexts={{ shot_1: "开场镜头" }}
          onRequestRefetch={vi.fn()}
          onRequestChange={vi.fn()}
        />,
      );
      expect(screen.getByText("开场镜头")).toBeInTheDocument();
    });
  });
});
