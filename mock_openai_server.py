"""
Local OpenAI-compatible mock server (dev/offline only).

Implements just enough of POST /v1/chat/completions for langchain-openai's
ChatOpenAI to talk to it, so the real LangGraph chat flow can run end-to-end
without a real OPENAI_API_KEY or outbound network. Echoes the user's last
message back as the assistant reply.

Run:  python mock_openai_server.py [port]   (default 8001)
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            req = {}

        messages = req.get("messages", [])
        last_user = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        reply = f"[mock-llm] You said: {last_user}"

        self._send(
            200,
            {
                "id": "chatcmpl-local-mock",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.get("model", "gpt-4o"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            },
        )

    def log_message(self, *args) -> None:  # noqa: D401 - silence default logging
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    print(f"mock OpenAI server listening on http://localhost:{port}/v1")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
