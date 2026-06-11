import { getSessionId } from "./session";

// All requests go to "/api", which the Vite dev server proxies to the
// FastAPI backend (see vite.config.ts).
const API_BASE = "/api";

export type ChatRequest = {
  message: string;
  session_id: string;
};

export type ChatResponse = {
  reply: string;
};

export type ReportRequest = {
  prompt: string;
  session_id: string;
};

export type ReportResponse = {
  report: string;
};

async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`Request failed (${res.status} ${res.statusText})`);
  }

  return (await res.json()) as TRes;
}

async function getJson<TRes>(path: string): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed (${res.status} ${res.statusText})`);
  }
  return (await res.json()) as TRes;
}

export function sendChatMessage(message: string): Promise<ChatResponse> {
  return postJson<ChatRequest, ChatResponse>("/chat", {
    message,
    session_id: getSessionId(),
  });
}

export function generateReport(prompt: string): Promise<ReportResponse> {
  return postJson<ReportRequest, ReportResponse>("/reports/generate", {
    prompt,
    session_id: getSessionId(),
  });
}

// ── Demo scaffold (shared DemoResponse schema) ──────────────────────────────

export type TableData = {
  columns: string[];
  rows: Array<Array<string | number | null>>;
};

export type Metric = { label: string; value: string; hint?: string | null };

export type AlertItem = {
  id: string;
  severity: string;
  source: string;
  title: string;
  description: string;
  recommended_action: string;
  reference_id?: string | null;
  vendor_name?: string | null;
  amount?: number | null;
  currency?: string | null;
  detected_at?: string | null;
};

export type ActionItem = { label: string; kind: string; hint?: string | null };

export type EvidenceItem = {
  source: string;
  snippet: string;
  doc_id?: string | null;
  score?: number | null;
};

export type DemoResponse = {
  intent: string;
  title: string;
  narrative: string;
  bullets: string[];
  metrics: Metric[];
  table?: TableData | null;
  alerts: AlertItem[];
  actions: ActionItem[];
  evidence: EvidenceItem[];
  data_scope: string[];
  confidence: number;
};

export const REPORT_TYPES: Array<{ id: string; label: string }> = [
  { id: "spend_analysis", label: "Spend Analysis" },
  { id: "vendor_performance", label: "Vendor Performance" },
  { id: "cash_flow_forecast", label: "Cash Flow Forecast" },
  { id: "entity_summary", label: "Entity Summary" },
  { id: "on_demand", label: "On-Demand Report" },
];

export function runDemoQuery(prompt: string): Promise<DemoResponse> {
  return postJson<{ prompt: string; session_id: string }, DemoResponse>(
    "/demo/query",
    { prompt, session_id: getSessionId() },
  );
}

export function generateDemoReport(
  reportType: string,
  target?: string,
  prompt?: string,
): Promise<DemoResponse> {
  return postJson<
    { report_type: string; target?: string; prompt?: string; session_id: string },
    DemoResponse
  >("/demo/report", {
    report_type: reportType,
    target,
    prompt,
    session_id: getSessionId(),
  });
}

export function fetchAlerts(limit = 12): Promise<DemoResponse> {
  return getJson<DemoResponse>(`/demo/alerts?limit=${limit}`);
}

export function fetchSummary(): Promise<DemoResponse> {
  return getJson<DemoResponse>("/demo/summary");
}
