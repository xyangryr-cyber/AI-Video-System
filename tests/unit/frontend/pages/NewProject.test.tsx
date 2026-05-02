import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { NewProject } from "@frontend/pages/NewProject";
import createResponse from "../../../fixtures/api/projects/create_response.json";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

const renderPage = () =>
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={["/projects/new"]}>
        <Routes>
          <Route path="/projects/new" element={<NewProject />} />
          <Route path="/projects/:id" element={<div>workflow page</div>} />
          <Route path="/projects/:id/phases/:phase" element={<div data-testid="phase-landing">phase-landing</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiClient.post).mockResolvedValue(createResponse);
});

describe("NewProject page", () => {
  it("AC-4 navigates to /projects/:id/phases/0 after success", async () => {
    renderPage();
    await userEvent.type(screen.getByLabelText(/标题/), "Ok");
    await userEvent.type(screen.getByLabelText(/描述/), "这是一个长度足够的项目描述");
    await userEvent.click(screen.getByRole("button", { name: /开始制作/ }));
    await screen.findByTestId("phase-landing");
  });

  it("shows error message when API fails", async () => {
    vi.mocked(apiClient.post).mockRejectedValue({
      error_code: "SERVER_ERROR",
      message: "服务器内部错误",
      status: 500,
    });
    renderPage();
    await userEvent.type(screen.getByLabelText(/标题/), "Test");
    await userEvent.type(screen.getByLabelText(/描述/), "这是一个长度足够的项目描述");
    await userEvent.click(screen.getByRole("button", { name: /开始制作/ }));
    await screen.findByRole("alert");
    expect(screen.getByRole("alert")).toHaveTextContent(/服务器内部错误/);
  });
});
