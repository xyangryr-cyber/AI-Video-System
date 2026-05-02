import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateProjectForm } from "@frontend/components/CreateProjectForm";

describe("CreateProjectForm", () => {
  it("AC-1 shows title and description inputs", () => {
    render(<CreateProjectForm onSubmit={vi.fn()} isSubmitting={false} />);
    expect(screen.getByLabelText(/标题/)).toBeInTheDocument();
    expect(screen.getByLabelText(/描述/)).toBeInTheDocument();
  });

  it("AC-2 blocks submit when description < 10 chars", async () => {
    const onSubmit = vi.fn();
    render(<CreateProjectForm onSubmit={onSubmit} isSubmitting={false} />);
    await userEvent.type(screen.getByLabelText(/标题/), "Test");
    await userEvent.type(screen.getByLabelText(/描述/), "太短");
    await userEvent.click(screen.getByRole("button", { name: /开始制作/ }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/至少 10 个字/);
  });

  it("AC-3 submits with title+description when valid", async () => {
    const onSubmit = vi.fn();
    render(<CreateProjectForm onSubmit={onSubmit} isSubmitting={false} />);
    await userEvent.type(screen.getByLabelText(/标题/), "Test Project");
    await userEvent.type(screen.getByLabelText(/描述/), "这是一个长度足够的项目描述");
    await userEvent.click(screen.getByRole("button", { name: /开始制作/ }));
    expect(onSubmit).toHaveBeenCalledWith({
      title: "Test Project",
      description: "这是一个长度足够的项目描述",
    });
  });
});
