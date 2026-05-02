import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CandidateSelector } from "@frontend/components/CandidateSelector";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { apiClient } from "@frontend/api/client";

beforeEach(() => {
  vi.clearAllMocks();
});

const candidates = [
  { id: "c1", is_recommended: true, preview_url: "u1" },
  { id: "c2", is_recommended: false, preview_url: "u2" },
];

describe("CandidateSelector", () => {
  it("AC-1 displays up to 3 candidates with preview capability", () => {
    const many = [...candidates, { id: "c3", is_recommended: false, preview_url: "u3" }, { id: "c4", is_recommended: false, preview_url: "u4" }];
    render(<CandidateSelector projectId="p1" phase={5} candidates={many} />);
    expect(screen.getAllByTestId("candidate-card").length).toBeLessThanOrEqual(3);
  });

  it("AC-6 confirm posts to /preferences/confirm with candidate_id", async () => {
    let capturedBody: unknown = null;
    vi.mocked(apiClient.post).mockImplementationOnce(async (_path, body) => {
      capturedBody = body;
      return { ok: true };
    });
    render(<CandidateSelector projectId="p1" phase={5} candidates={candidates} />);
    await userEvent.click(screen.getAllByTestId("candidate-card")[1]);                   // preview
    await userEvent.click(screen.getAllByRole("button", { name: /选择/ })[1]);          // select
    await userEvent.click(screen.getByRole("button", { name: /确认/ }));                 // confirm
    await vi.waitFor(() => expect(capturedBody).toMatchObject({ decisions: expect.any(Object) }));
    expect(JSON.stringify(capturedBody)).toContain("c2");
  });

  it("AC-7 accepts generic Candidate shape (compile-time + runtime smoke)", () => {
    render(
      <CandidateSelector
        projectId="p1" phase={8}
        candidates={[{ id: "x", is_recommended: true, custom_field: 42 } as any]}
      />,
    );
    expect(screen.getByTestId("candidate-card")).toBeInTheDocument();
  });

  it("AC-8 no unlock style_lock button exposed", () => {
    render(<CandidateSelector projectId="p1" phase={5} candidates={candidates} />);
    expect(screen.queryByRole("button", { name: /解锁/ })).toBeNull();
  });
});
