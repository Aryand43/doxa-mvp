import { describe, it, expect, vi, beforeEach } from "vitest";
import { runQuery } from "./api";

describe("runQuery (AI query API contract)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("POSTs the prompt to /api/ai/query and returns the parsed AIResponse", async () => {
    const payload = { mode: "assistant", intent: "approvals", title: "Pending" };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      text: async () => JSON.stringify(payload),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await runQuery("What is pending?");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/ai/query");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.prompt).toBe("What is pending?");
    expect(typeof body.session_id).toBe("string");
    expect(result).toMatchObject({ mode: "assistant", intent: "approvals" });
  });
});
