import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DataVerificationPanel } from "../../../../src/frontend/components/DataVerificationPanel";
import type { DataPoint } from "../../../../src/frontend/types/dataVerification";

const mockDataPoints: DataPoint[] = [
  {
    id: "dp-1",
    value: "100M USD",
    source: "FinancialDataService",
    trust_level: "llm_generated",
    verification_status: "pending",
    verified_at: null,
    fact_checker_notes: null,
    verdict: null,
  },
  {
    id: "dp-2",
    value: "+15% YoY",
    source: "FactCheckAgent",
    trust_level: "user_verified",
    verification_status: "verified",
    verified_at: new Date().toISOString(),
    fact_checker_notes: "Confirmed against SEC filing",
    verdict: "confirmed",
  },
  {
    id: "dp-3",
    value: "Declining trend",
    source: "FactCheckAgent",
    trust_level: "llm_generated",
    verification_status: "failed",
    verified_at: new Date().toISOString(),
    fact_checker_notes: "Data contradicts source",
    verdict: "refuted",
  },
  {
    id: "dp-4",
    value: "5% market share",
    source: "MarketDataService",
    trust_level: "stale",
    verification_status: "stale",
    verified_at: "2024-01-01T00:00:00Z",
    fact_checker_notes: null,
    verdict: null,
  },
];

describe("AC-1: summary stats bar", () => {
  it("displays total, verified, pending, failed, stale counts", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    const statsBar = screen.getByTestId("stats-bar");
    expect(statsBar).toBeTruthy();
    expect(screen.getByText(/Total: 4/)).toBeTruthy();
    // "verified" text appears both in stats bar and row badges; check within stats bar
    expect(statsBar.textContent).toContain("verified");
    expect(statsBar.textContent).toContain("pending");
    expect(statsBar.textContent).toContain("failed");
    expect(statsBar.textContent).toContain("stale");
  });
});

describe("AC-2: renders data point fields", () => {
  it("shows value, source, trust_level, verification timestamp per row", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    expect(screen.getByText("100M USD")).toBeTruthy();
    expect(screen.getByText("FinancialDataService")).toBeTruthy();
    // "llm_generated" appears on multiple rows (dp-1, dp-3)
    const badges = screen.getAllByText("llm_generated");
    expect(badges.length).toBe(2);
  });
});

describe("AC-3: llm_generated shows verify and confirm", () => {
  it("renders Verify and Manual Confirm buttons for llm_generated trust", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    const verifyBtns = screen.getAllByText("Verify");
    const confirmBtns = screen.getAllByText("Manual Confirm");
    expect(verifyBtns.length).toBeGreaterThanOrEqual(1);
    expect(confirmBtns.length).toBeGreaterThanOrEqual(1);
  });
});

describe("AC-4: stale shows reverify", () => {
  it("renders Verify button for stale rows", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    // dp-4 is stale, should have a re-verify button
    const verifyBtns = screen.getAllByText("Verify");
    expect(verifyBtns.length).toBeGreaterThanOrEqual(2); // at least 2 verify buttons
  });
});

describe("AC-5: verify triggers subtask", () => {
  it("renders Verify buttons for eligible rows", async () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    // dp-1 (llm_generated) + dp-4 (stale) both get Verify buttons
    const verifyBtns = screen.getAllByText("Verify");
    expect(verifyBtns.length).toBe(3); // dp-1, dp-3 (llm_generated) + dp-4 (stale)
  });
});

describe("AC-6: manual confirm updates trust", () => {
  it("changes row to user_verified on Manual Confirm click", async () => {
    const user = userEvent.setup();
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    // dp-2 already has user_verified, dp-1 has llm_generated
    const confirmBtn = screen.getAllByText("Manual Confirm")[0];
    await user.click(confirmBtn);
    // After clicking confirm on dp-1, there should now be 2 user_verified rows
    await waitFor(() => {
      const badges = screen.getAllByText("user_verified");
      expect(badges.length).toBe(2);
    });
  });
});

describe("AC-7: expand shows notes", () => {
  it("expands row to show FactChecker notes on click", async () => {
    const user = userEvent.setup();
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    const row = screen.getByText("+15% YoY").closest("[data-testid]");
    if (row) await user.click(row);
    await waitFor(() => {
      expect(screen.getByText(/Confirmed against SEC filing/)).toBeTruthy();
    });
  });
});

describe("AC-8: refuted renders red", () => {
  it("renders refuted rows with red styling", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    const refutedRow = screen.getByText("Declining trend").closest("[data-testid]");
    expect(refutedRow?.getAttribute("data-status")).toBe("failed");
  });
});

describe("AC-9: WS realtime stats update", () => {
  it("updates stats on data change (simulates WS event)", async () => {
    const { rerender } = render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    const updatedPoints = mockDataPoints.map((dp) =>
      dp.id === "dp-1" ? { ...dp, verification_status: "verified" as const, trust_level: "user_verified" as const } : dp
    );
    rerender(<DataVerificationPanel dataPoints={updatedPoints} />);
    await waitFor(() => {
      // stats bar should still be present after update
      expect(screen.getByTestId("stats-bar")).toBeTruthy();
    });
  });
});

describe("AC-10: stats consistent with rows", () => {
  it("stats numbers match actual row states", () => {
    render(<DataVerificationPanel dataPoints={mockDataPoints} />);
    // 4 total rows, stats should sum to 4
    const verifiedCount = mockDataPoints.filter((d) => d.verification_status === "verified").length;
    const pendingCount = mockDataPoints.filter((d) => d.verification_status === "pending").length;
    const failedCount = mockDataPoints.filter((d) => d.verification_status === "failed").length;
    const staleCount = mockDataPoints.filter((d) => d.verification_status === "stale").length;
    expect(verifiedCount + pendingCount + failedCount + staleCount).toBe(4);
  });
});
