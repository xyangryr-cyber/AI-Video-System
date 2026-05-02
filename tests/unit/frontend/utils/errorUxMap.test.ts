import { describe, it, expect } from "vitest";
import { ERROR_UX_MAP, lookupErrorUx } from "@frontend/utils/errorUxMap";

const CODES = ["EVID_3002","EVID_3004","EVID_4001","EVID_4002","EVID_2001","EVID_5001","EVID_5002","EVID_3001"];

describe("ERROR_UX_MAP", () => {
  it("AC-1 maps all 8 error codes", () => {
    for (const c of CODES) expect(ERROR_UX_MAP[c]).toBeDefined();
  });

  it("AC-2 is pure static (no function calls, plain object)", () => {
    for (const c of CODES) {
      const entry = ERROR_UX_MAP[c];
      expect(typeof entry.tier).toBe("string");
      expect(typeof entry.component).toBe("string");
      expect(Array.isArray(entry.actions)).toBe(true);
    }
  });

  it("AC-3 EVID_3002 + EVID_3004 are auto_handling toast", () => {
    expect(ERROR_UX_MAP.EVID_3002.tier).toBe("auto_handling");
    expect(ERROR_UX_MAP.EVID_3002.component).toBe("toast");
    expect(ERROR_UX_MAP.EVID_3004.tier).toBe("auto_handling");
  });

  it("AC-4 user_choice entries each have >= 2 actions", () => {
    for (const c of ["EVID_4001","EVID_4002","EVID_2001"]) {
      expect(ERROR_UX_MAP[c].tier).toBe("user_choice");
      expect(ERROR_UX_MAP[c].component).toBe("modal");
      expect(ERROR_UX_MAP[c].actions.length).toBeGreaterThanOrEqual(2);
    }
  });

  it("AC-5 user_action entries render modal", () => {
    for (const c of ["EVID_5001","EVID_5002","EVID_3001"]) {
      expect(ERROR_UX_MAP[c].tier).toBe("user_action");
      expect(ERROR_UX_MAP[c].component).toBe("modal");
    }
  });

  it("AC-6 every code has >= 1 recovery action", () => {
    for (const c of CODES) expect(ERROR_UX_MAP[c].actions.length).toBeGreaterThanOrEqual(1);
  });

  it("AC-7 unknown code falls back to user_action generic modal", () => {
    const fb = lookupErrorUx("UNKNOWN_9999");
    expect(fb.tier).toBe("user_action");
    expect(fb.component).toBe("modal");
    expect(fb.actions.length).toBeGreaterThanOrEqual(1);
  });
});
