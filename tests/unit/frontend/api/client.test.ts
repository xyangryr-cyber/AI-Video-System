import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiClient } from "@frontend/api/client";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("apiClient", () => {
  it("GET returns parsed JSON body for 2xx", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ project_id: "proj_001" }]), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    ));

    const data = await apiClient.get<Array<{ project_id: string }>>("/api/projects");
    expect(Array.isArray(data)).toBe(true);
    expect(data[0].project_id).toBe("proj_001");
  });

  it("throws ApiError with code on 4xx", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error_code: "EVID_4001", message: "not found" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      })
    ));

    await expect(apiClient.get("/api/nope")).rejects.toMatchObject({
      error_code: "EVID_4001",
      status: 404,
    });
  });

  it("POST serializes JSON body and sends content-type header", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", mockFetch);

    await apiClient.post("/api/echo", { a: 1 });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [_path, init] = mockFetch.mock.calls[0];
    expect(init.headers["content-type"]).toContain("application/json");
    expect(JSON.parse(init.body)).toEqual({ a: 1 });
  });
});
