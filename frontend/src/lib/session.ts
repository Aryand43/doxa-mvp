// Shared in-memory session id, reused across all API requests for the
// lifetime of the page. Resets on full reload (matches backend MemorySaver,
// which is in-process and non-persistent).
let sessionId: string | null = null;

export function getSessionId(): string {
  if (sessionId === null) {
    sessionId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
  return sessionId;
}
