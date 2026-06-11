// Single typed API client for Doxa Connex AI. All product data comes from here.

import type { AIResponse, CrawlResponse, ReportType } from "./types";

const API_BASE = "/api/ai";

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

async function post<TRes>(path: string, body: unknown): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status} ${res.statusText})`);
  return (await res.json()) as TRes;
}

async function get<TRes>(path: string): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status} ${res.statusText})`);
  return (await res.json()) as TRes;
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
