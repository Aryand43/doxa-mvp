import { describe, it, expect } from "vitest";
import { hasAuthority, formatTenantLabel } from "./auth";
import type { AuthInfo } from "./types";

const baseUser: AuthInfo = {
  user_id: "test-user",
  companies: ["tenant-a", "tenant-b"],
  authorities: ["AI:read"],
  roles: ["USER"],
  auth_required: true,
};

describe("hasAuthority", () => {
  it("matches exact authority", () => {
    expect(hasAuthority(baseUser, "AI:read")).toBe(true);
    expect(hasAuthority(baseUser, "REPORT:read")).toBe(false);
  });

  it("supports wildcard authorities", () => {
    expect(hasAuthority({ ...baseUser, authorities: ["*"] }, "CRAWLER:read")).toBe(true);
    expect(hasAuthority({ ...baseUser, authorities: ["AI:*"] }, "AI:read")).toBe(true);
    expect(hasAuthority({ ...baseUser, authorities: ["*:read"] }, "REPORT:read")).toBe(true);
  });
});

describe("formatTenantLabel", () => {
  it("shows single tenant or count suffix", () => {
    expect(formatTenantLabel(["tenant-a"])).toBe("tenant-a");
    expect(formatTenantLabel(["tenant-a", "tenant-b"])).toBe("tenant-a (+1)");
    expect(formatTenantLabel([])).toBe("No tenant");
  });
});
