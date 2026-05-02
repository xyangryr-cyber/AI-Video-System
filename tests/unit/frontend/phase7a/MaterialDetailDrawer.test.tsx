import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MaterialDetailDrawer } from "@frontend/components/phase7a/MaterialDetailDrawer";

describe("MaterialDetailDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-2: renders drawer with refetch button", () => {
    it("renders material id and status", () => {
      render(
        <MaterialDetailDrawer
          materialId="mat_2"
          status="missing"
          rationale="数据源不可用"
          source="东方财富API"
          evidence="HTTP 503"
          onRequestRefetch={vi.fn()}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText("mat_2")).toBeInTheDocument();
      expect(screen.getByText(/missing|缺失/)).toBeInTheDocument();
    });

    it("shows rationale, source, and evidence", () => {
      render(
        <MaterialDetailDrawer
          materialId="mat_2"
          status="missing"
          rationale="数据源不可用"
          source="东方财富API"
          evidence="HTTP 503"
          onRequestRefetch={vi.fn()}
          onClose={vi.fn()}
        />,
      );
      expect(screen.getByText(/数据源不可用/)).toBeInTheDocument();
      expect(screen.getByText(/东方财富API/)).toBeInTheDocument();
      expect(screen.getByText(/HTTP 503/)).toBeInTheDocument();
    });

    it("calls onRequestRefetch when refetch button clicked", () => {
      const onRefetch = vi.fn();
      render(
        <MaterialDetailDrawer
          materialId="mat_2"
          status="missing"
          rationale="..."
          source="..."
          evidence="..."
          onRequestRefetch={onRefetch}
          onClose={vi.fn()}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /重抓|refetch/i }));
      expect(onRefetch).toHaveBeenCalledWith("mat_2");
    });

    it("calls onClose when close button clicked", () => {
      const onClose = vi.fn();
      render(
        <MaterialDetailDrawer
          materialId="mat_2"
          status="missing"
          rationale="..."
          source="..."
          evidence="..."
          onRequestRefetch={vi.fn()}
          onClose={onClose}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /关闭|close/i }));
      expect(onClose).toHaveBeenCalled();
    });
  });
});
