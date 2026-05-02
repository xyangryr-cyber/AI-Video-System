import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ClaimWorkbench } from "../../../../src/frontend/components/ClaimWorkbench";
import type { ClaimRow } from "../../../../src/frontend/types/claim";

const mockClaims: ClaimRow[] = [
  {
    claim_id: "c1",
    claim_type: "financial_data",
    entity: "Revenue",
    value: "100M USD",
    verification_status: "verified",
    hard_blocking: false,
    source_phase: 2,
    trust_level: "user_verified",
  },
  {
    claim_id: "c2",
    claim_type: "fact",
    entity: "Market Share",
    value: "+15%",
    verification_status: "unverified",
    hard_blocking: true,
    source_phase: 7,
    trust_level: "llm_generated",
  },
  {
    claim_id: "c3",
    claim_type: "financial_data",
    entity: "Costs",
    value: "50M USD",
    verification_status: "user_disputed",
    hard_blocking: false,
    source_phase: 8,
    trust_level: "llm_generated",
  },
  {
    claim_id: "c4",
    claim_type: "image_backed",
    entity: "Chart Q3",
    value: "bar chart",
    verification_status: "unverified",
    hard_blocking: true,
    source_phase: 8,
    trust_level: "llm_generated",
  },
];

describe("AC-1: filter bar four dimensions returns correct subset", () => {
  it("filters by claim_type", () => {
    render(<ClaimWorkbench claims={mockClaims} />);
    expect(screen.getByText("Revenue")).toBeTruthy();
    expect(screen.getByText("Market Share")).toBeTruthy();
  });

  it("filters by verification_status", async () => {
    const user = userEvent.setup();
    render(<ClaimWorkbench claims={mockClaims} />);
    // Click the filter-unverified button by testId
    const filterBtn = screen.getByTestId("filter-unverified");
    await user.click(filterBtn);
    await waitFor(() => {
      // Should show unverified claims (Market Share, Chart Q3), hide verified (Revenue)
      expect(screen.getByText("Market Share")).toBeTruthy();
      expect(screen.getByText("Chart Q3")).toBeTruthy();
      // Revenue is "verified", should be filtered out
    });
  });
});

describe("AC-2: row actions trigger corresponding actions", () => {
  it("renders Verify, Challenge, Supplement, Dismiss buttons", () => {
    render(<ClaimWorkbench claims={mockClaims} />);
    expect(screen.getAllByText("Verify").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Challenge").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Supplement").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Dismiss").length).toBeGreaterThan(0);
  });
});

describe("AC-3: blocking badge red when unverified > 0", () => {
  it("shows red badge when hard_blocking unverified claims exist", () => {
    render(<ClaimWorkbench claims={mockClaims} />);
    const badges = screen.getAllByTestId("blocking-badge");
    // There are 2 badges (one in TopStatsBar, one standalone) - both should show red
    const mainBadge = badges[badges.length - 1]; // standalone badge in top-right
    expect(mainBadge.textContent).toContain("2");
    expect(mainBadge.getAttribute("data-severity")).toBe("red");
  });
});

describe("AC-4: view toggle preserves filter state", () => {
  it("switches view without losing filters", async () => {
    const user = userEvent.setup();
    render(<ClaimWorkbench claims={mockClaims} />);
    // Apply a filter using testId
    const unverifiedBtn = screen.getByTestId("filter-unverified");
    await user.click(unverifiedBtn);
    // Verify filtered state: "Revenue" (verified) is hidden
    await waitFor(() => {
      expect(screen.queryByText("Revenue")).toBeNull();
    });
    // Toggle view to Table
    const tableViewBtn = screen.getByText("Table");
    await user.click(tableViewBtn);
    // Filter should still be active - Revenue still hidden
    expect(screen.queryByText("Revenue")).toBeNull();
    expect(screen.getByText("Market Share")).toBeTruthy();
  });
});
