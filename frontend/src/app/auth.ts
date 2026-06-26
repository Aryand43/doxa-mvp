import type { AuthInfo } from "./types";

/** Backend authority strings — see backend/AUTH_README.md */
export const AUTHORITY = {
  AI_READ: "AI:read",
  REPORT_READ: "REPORT:read",
  CRAWLER_READ: "CRAWLER:read",
} as const;

export type Authority = (typeof AUTHORITY)[keyof typeof AUTHORITY];

/** Match backend wildcard rules (`*`, `AI:*`, `*:read`). */
export function hasAuthority(user: AuthInfo, required: Authority | string): boolean {
  const authorities = user.authorities ?? [];
  if (authorities.includes("*")) return true;
  if (authorities.includes(required)) return true;

  const [module, action] = required.split(":");
  if (module && authorities.includes(`${module}:*`)) return true;
  if (action && authorities.includes(`*:${action}`)) return true;
  return false;
}

export function formatTenantLabel(companies: string[]): string {
  if (!companies.length) return "No tenant";
  if (companies.length === 1) return companies[0];
  return `${companies[0]} (+${companies.length - 1})`;
}

export function isForbiddenError(err: unknown): boolean {
  return err instanceof Error && "status" in err && (err as { status: number }).status === 403;
}
