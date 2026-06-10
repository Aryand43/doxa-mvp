import { describe, it, expect, vi, beforeEach } from "vitest";
import { sendChatMessage } from "./api";

// Mock the session helper at its own boundary so the session value is
// deterministic; this test does not exercise id generation.
vi.mock("./session", () => ({
  getSessionId: () => "test-session-123",
}));

describe("sendChatMessage (Chat API contract)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("POSTs the backend-shaped body to /api/chat and parses { reply }", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ reply: "Hello from the backend." }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await sendChatMessage("Hi there");

    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/chat");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({
      message: "Hi there",
      session_id: "test-session-123",
    });

    expect(result).toEqual({ reply: "Hello from the backend." });
  });
});
