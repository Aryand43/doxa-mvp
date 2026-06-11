import { useState, type FormEvent } from "react";
import { Card } from "../../components/Card";
import { ResponseView } from "../../components/ResponseView";
import { runDemoQuery, type DemoResponse } from "../../lib/api";

const QUICK_PROMPTS = [
  "What POs are pending my approval today?",
  "Which suppliers have high rejection or risk signals?",
  "Show invoices with duplicate/fraud/anomaly risk",
  "Give me a cash flow summary based on invoices and payments",
  "What contracts are approaching expiry?",
];

export function ChatPanel() {
  const [input, setInput] = useState("");
  const [prompt, setPrompt] = useState<string | null>(null);
  const [response, setResponse] = useState<DemoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(text: string) {
    const query = text.trim();
    if (!query || loading) return;

    setPrompt(query);
    setInput("");
    setError(null);
    setResponse(null);
    setLoading(true);

    try {
      const data = await runDemoQuery(query);
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get an answer.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    void ask(input);
  }

  return (
    <Card title="AI Assistant">
      <div className="chat-panel">
        <div className="chip-row">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              className="chip"
              onClick={() => void ask(p)}
              disabled={loading}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="chat-output">
          {prompt && <p className="chat-question">{prompt}</p>}
          {loading && <p className="placeholder">Analyzing procurement data…</p>}
          {error && <p className="chat-error">{error}</p>}
          {response && !loading && <ResponseView data={response} />}
          {!prompt && !loading && !error && (
            <p className="placeholder">
              Ask about approvals, spend, vendor risk, anomalies, cash flow, or
              contracts — or tap a prompt above.
            </p>
          )}
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask the assistant…"
            aria-label="Message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || input.trim() === ""}>
            Ask
          </button>
        </form>
      </div>
    </Card>
  );
}
