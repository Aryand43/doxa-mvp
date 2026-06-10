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
