import { describe, it, expect } from "vitest";
import { createQueryClient } from "@frontend/lib/queryClient";

describe("createQueryClient", () => {
  it("returns a QueryClient with test-friendly defaults", () => {
    const qc = createQueryClient();
    const defaults = qc.getDefaultOptions();
    expect(defaults.queries?.retry).toBe(false);
    expect(defaults.queries?.staleTime).toBe(0);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
  });
});
