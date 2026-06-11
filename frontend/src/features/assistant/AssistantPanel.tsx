import { useState, type FormEvent } from "react";
import { runQuery } from "../../app/api";
import type { AIResponse } from "../../app/types";
import { Panel } from "../../components/Panel";
import { ResponseCard } from "../../components/ResponseCard";
import { PromptChips } from "../../components/PromptChips";
import { LoadingState } from "../../components/LoadingState";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import styles from "./AssistantPanel.module.css";

const QUICK_PROMPTS = [
  "What POs are pending my approval today?",
  "Which suppliers have the highest rejection or risk signals?",
  "Show invoices with duplicate/fraud/anomaly risk",
  "Which invoices are overdue?",
  "Summarize committed vs actual spend for Project SI-2422",
  "Give me a cash flow summary based on invoices and payments",
  "What contracts are approaching expiry?",
  "Who are our top vendors by spend?",
  "What can you help me with?",
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
      setError(err instanceof Error ? err.message : "The assistant did not respond.");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void ask(input);
  }

  return (
    <Panel
      kicker="Ask"
      title="AI Assistant"
      description="Ask in plain language — approvals, spend, vendors, invoices, cash flow, contracts, or a general overview."
      controls={<PromptChips prompts={QUICK_PROMPTS} onSelect={(p) => void ask(p)} disabled={loading} />}
      footer={
        <form className={styles.bar} onSubmit={onSubmit}>
          <input
            type="text"
            placeholder="Ask anything about approvals, spend, vendors, invoices, cash flow, contracts…"
            aria-label="Message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || input.trim() === ""}>
            Ask
          </button>
        </form>
      }
    >
      {question && <p className={styles.question}>{question}</p>}
      {loading && <LoadingState label="Reading the data" />}
      {error && (
        <ErrorState
          title="The assistant couldn't answer."
          message={error}
          onRetry={question ? () => void ask(question) : undefined}
        />
      )}
      {response && !loading && <ResponseCard data={response} />}
      {!question && !loading && !error && (
        <EmptyState
          title="Ask a question to get a grounded answer."
          message="Pick a starting point above, or type your own — every answer is backed by your data."
        />
      )}
    </Panel>
  );
}
