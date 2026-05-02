import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorToast } from "@frontend/components/errors/ErrorToast";

describe("ErrorToast", () => {
  it("renders ETA and non-modal layout", () => {
    render(<ErrorToast code="EVID_3002" message="Agent 超时" etaSec={5} />);
    expect(screen.getByText(/Agent 超时/)).toBeInTheDocument();
    expect(screen.getByText(/5s/)).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
