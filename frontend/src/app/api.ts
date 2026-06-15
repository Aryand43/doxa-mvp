// Single typed API client for Doxa Connex AI. All product data comes from here.

import type { AIResponse, CrawlResponse, ReportType } from "./types";
import { isApiDebugEnabled, recordApiCall, setBackendHealth } from "./apiDebug";

function apiRoot(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
}

function aiBase(): string {
  const root = apiRoot();
  return root ? `${root}/api/ai` : "/api/ai";
}

/** Full URL for the backend liveness probe (used by the API Inspector). */
export function healthUrl(): string {
  const root = apiRoot();
  return root ? `${root}/health` : "/health";
}

/** Scalar API reference URL on the same host as the API. */
export function scalarUrl(): string {
  const root = apiRoot();
  return root ? `${root}/scalar` : "/scalar";
}

// In-memory session id, reused for the page lifetime (resets on reload to match
// the backend's in-process state).
let sessionId: string | null = null;

function getSessionId(): string {
  if (sessionId === null) {
    sessionId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
  return sessionId;
}

async function parseJsonBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

async function request<TRes>(
  method: "GET" | "POST",
  url: string,
  body?: unknown,
): Promise<TRes> {
  const started = performance.now();
  const init: RequestInit = { method };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(url, init);
    const durationMs = Math.round(performance.now() - started);
    const responseBody = await parseJsonBody(res);

    if (isApiDebugEnabled()) {
      recordApiCall({
        method,
        url,
        requestBody: body,
        status: res.status,
        responseBody,
        durationMs,
        ok: res.ok,
        error: res.ok ? undefined : `${res.status} ${res.statusText}`,
      });
    }

    if (!res.ok) {
      throw new Error(`Request failed (${res.status} ${res.statusText})`);
    }

    return responseBody as TRes;
  } catch (err) {
    const durationMs = Math.round(performance.now() - started);
    const message = err instanceof Error ? err.message : String(err);

    if (isApiDebugEnabled()) {
      recordApiCall({
        method,
        url,
        requestBody: body,
        durationMs,
        ok: false,
        error: message,
      });
    }

    throw err;
  }
}

async function post<TRes>(path: string, body: unknown): Promise<TRes> {
  return request<TRes>("POST", `${aiBase()}${path}`, body);
}

async function get<TRes>(path: string): Promise<TRes> {
  return request<TRes>("GET", `${aiBase()}${path}`);
}

export function runQuery(prompt: string, explain = true): Promise<AIResponse> {
  return post<AIResponse>("/query", { prompt, session_id: getSessionId(), explain });
}

export function generateReport(
  reportType: string,
  target?: string,
  prompt?: string,
): Promise<AIResponse> {
  return post<AIResponse>("/report", {
    report_type: reportType,
    target,
    prompt,
    session_id: getSessionId(),
  });
}

export function runCrawl(windowDays = 60, explain = true): Promise<CrawlResponse> {
  return post<CrawlResponse>("/crawl", {
    window_days: windowDays,
    explain,
    session_id: getSessionId(),
  });
}

export function fetchSummary(): Promise<AIResponse> {
  return get<AIResponse>("/summary");
}

export async function fetchReportTypes(): Promise<ReportType[]> {
  const data = await get<{ report_types: ReportType[] }>("/report-types");
  return data.report_types;
}

/** Probe backend liveness — never throws; updates inspector health state. */
export async function checkBackendHealth(): Promise<"healthy" | "unhealthy"> {
  const url = healthUrl();
  const started = performance.now();

  try {
    const res = await fetch(url, { method: "GET" });
    const durationMs = Math.round(performance.now() - started);
    const responseBody = await parseJsonBody(res);
    const healthy =
      res.ok &&
      typeof responseBody === "object" &&
      responseBody !== null &&
      (responseBody as { status?: string }).status === "ok";

    if (isApiDebugEnabled()) {
      recordApiCall({
        method: "GET",
        url,
        status: res.status,
        responseBody,
        durationMs,
        ok: healthy,
        error: healthy ? undefined : "Health check failed",
      });
    }

    const status = healthy ? "healthy" : "unhealthy";
    setBackendHealth(status);
    return status;
  } catch (err) {
    const durationMs = Math.round(performance.now() - started);
    const message = err instanceof Error ? err.message : String(err);

    if (isApiDebugEnabled()) {
      recordApiCall({
        method: "GET",
        url,
        durationMs,
        ok: false,
        error: message,
      });
    }

    setBackendHealth("unhealthy");
    return "unhealthy";
  }
}
