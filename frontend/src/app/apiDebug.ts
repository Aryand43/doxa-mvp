/** Lightweight API transport debugger — no external deps, easy to remove. */

export type ApiCallRecord = {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  requestBody?: unknown;
  status?: number;
  responseBody?: unknown;
  durationMs: number;
  ok: boolean;
  error?: string;
};

export type BackendHealth = "healthy" | "unhealthy" | "unknown";

const MAX_RECORDS = 50;

const calls: ApiCallRecord[] = [];
const listeners = new Set<() => void>();
let backendHealth: BackendHealth = "unknown";

export function isApiDebugEnabled(): boolean {
  return import.meta.env.DEV || import.meta.env.VITE_ENABLE_API_DEBUG === "true";
}

export function subscribeApiDebug(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notify(): void {
  listeners.forEach((listener) => listener());
}

export function getApiCalls(): ApiCallRecord[] {
  return [...calls];
}

export function clearApiCalls(): void {
  calls.length = 0;
  notify();
}

export function getBackendHealth(): BackendHealth {
  return backendHealth;
}

export function setBackendHealth(status: BackendHealth): void {
  backendHealth = status;
  notify();
}

export function recordApiCall(
  record: Omit<ApiCallRecord, "id" | "timestamp"> & { id?: string },
): ApiCallRecord {
  const entry: ApiCallRecord = {
    id: record.id ?? crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    ...record,
  };

  calls.unshift(entry);
  if (calls.length > MAX_RECORDS) calls.pop();

  if (isApiDebugEnabled()) {
    const label = record.ok
      ? `${record.method} ${record.url} → ${record.status} (${record.durationMs}ms)`
      : `${record.method} ${record.url} → FAILED (${record.durationMs}ms)`;
    console.groupCollapsed(`[API] ${label}`);
    if (record.requestBody !== undefined) console.log("Request:", record.requestBody);
    if (record.responseBody !== undefined) console.log("Response:", record.responseBody);
    if (record.error) console.warn("Error:", record.error);
    console.groupEnd();
  }

  notify();
  return entry;
}
