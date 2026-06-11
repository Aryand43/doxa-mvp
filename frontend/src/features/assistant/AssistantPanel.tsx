import { useState, type FormEvent } from "react";
import { runQuery } from "../../app/api";
import type { AIResponse } from "../../app/types";
import { ResponseCard } from "../../components/ResponseCard";
import { PromptChips } from "../../components/PromptChips";
import { LoadingState } from "../../components/LoadingState";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";

const QUICK_PROMPTS = [
  "What POs are pending my approval today?",
  "Which suppliers have the highest rejection or risk signals?",
  "Show invoices with duplicate/fraud/anomaly risk",
  "Give me a cash flow summary based on invoices and payments",
  "What contracts are approaching expiry?",
];

export function AssistantPanel() {
  const [input, setInput] = useState("");
  const [question, setQuestion] = useState<string | null>(null);
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(text: string) {
    const prompt = text.trim();
    if (!prompt || loading) return;
    setQuestion(prompt);
    setInput("");
    setError(null);
    setResponse(null);
    setLoading(true);
    try {
      setResponse(await runQuery(prompt));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get an answer.");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void ask(input);
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <h2>AI Assistant</h2>
        <p>Ask anything about your procurement data.</p>
      </header>

      <PromptChips prompts={QUICK_PROMPTS} onSelect={(p) => void ask(p)} disabled={loading} />

      <div className="panel-output">
        {question && <p className="user-question">{question}</p>}
        {loading && <LoadingState label="Analyzing procurement data…" />}
        {error && <ErrorState message={error} />}
        {response && !loading && <ResponseCard data={response} />}
        {!question && !loading && !error && (
          <EmptyState message="Ask about approvals, spend, vendor risk, anomalies, cash flow, or contracts — or tap a prompt above." />
        )}
      </div>

      <form className="prompt-bar" onSubmit={onSubmit}>
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
    </section>
  );
}
