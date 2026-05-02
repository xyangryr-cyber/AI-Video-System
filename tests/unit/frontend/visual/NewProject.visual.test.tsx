import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateProjectForm } from "@frontend/components/CreateProjectForm";

describe("CreateProjectForm visual alignment", () => {
  it("renders the form card with border-2 border-slate-200 rounded-2xl", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    const form = document.querySelector("form");
    expect(form?.className).toMatch(/border-2/);
    expect(form?.className).toMatch(/border-slate-200/);
    expect(form?.className).toMatch(/rounded-2xl/);
  });

  it("renders Chinese label '项目标题'", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByText("项目标题")).toBeDefined();
  });

  it("renders Chinese label containing '内容主题描述'", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByText(/内容主题描述/)).toBeDefined();
  });

  it("renders '开始制作' submit button with blue styling", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    const btn = screen.getByText("开始制作");
    expect(btn.tagName).toBe("BUTTON");
    expect(btn.className).toMatch(/bg-blue-600/);
  });

  it("renders '取消' button", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByText("取消")).toBeDefined();
  });

  it("renders character counter showing '/ 2000'", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByText(/\/ 2000/)).toBeDefined();
  });

  it("shows '至少 10 个字符' hint", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByText("至少 10 个字符")).toBeDefined();
  });

  it("submit button is disabled when title is empty", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    const btn = screen.getByText("开始制作").closest("button")!;
    expect(btn.disabled).toBe(true);
  });

  it("character counter turns red when description is short", async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    const textarea = screen.getByLabelText(/内容主题描述/);
    await user.type(textarea, "abc");
    const hint = screen.getByText("至少 10 个字符");
    expect(hint.className).toMatch(/text-red-500/);
  });
});
