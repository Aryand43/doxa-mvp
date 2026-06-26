import { useEffect, useRef, useState, type FormEvent } from "react";
import { runQuery } from "../../app/api";
import type { AIResponse } from "../../app/types";
import { Panel } from "../../components/Panel";
import { PromptChips } from "../../components/PromptChips";
import { EmptyState } from "../../components/EmptyState";
import {
  AssistantMessage,
  ErrorMessage,
  TypingIndicator,
  UserMessage,
} from "./ChatMessage";
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

type ChatItem =
  | { id: string; kind: "user"; text: string }
  | { id: string; kind: "assistant"; response: AIResponse }
  | { id: string; kind: "error"; text: string; retryPrompt: string };

function nextId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AssistantPanel() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [loading, setLoading] = useState(false);
  const threadEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function ask(text: string) {
    const prompt = text.trim();
    if (!prompt || loading) return;

    setMessages((current) => [...current, { id: nextId(), kind: "user", text: prompt }]);
    setInput("");
    setLoading(true);

    try {
      const response = await runQuery(prompt);
      setMessages((current) => [...current, { id: nextId(), kind: "assistant", response }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "The assistant did not respond.";
      setMessages((current) => [
        ...current,
        { id: nextId(), kind: "error", text: message, retryPrompt: prompt },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void ask(input);
  }

  const hasMessages = messages.length > 0 || loading;

  return (
    <Panel
      kicker="Ask"
      title="AI Assistant"
      description="Ask in plain language — approvals, spend, vendors, invoices, cash flow, contracts, or a general overview."
      controls={<PromptChips prompts={QUICK_PROMPTS} onSelect={(p) => void ask(p)} disabled={loading} />}
      footer={
        <form className={styles.composer} onSubmit={onSubmit}>
          <input
            type="text"
            placeholder="Message the assistant…"
            aria-label="Message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || input.trim() === ""}>
            Send
          </button>
        </form>
      }
    >
      <div className={styles.thread}>
        {!hasMessages && (
          <EmptyState
            title="Start a conversation"
            message="Pick a prompt above or type a question — every answer is grounded in your procurement data."
          />
        )}

        {messages.map((message) => {
          if (message.kind === "user") {
            return <UserMessage key={message.id} text={message.text} />;
          }
          if (message.kind === "assistant") {
            return <AssistantMessage key={message.id} data={message.response} />;
          }
          return (
            <ErrorMessage
              key={message.id}
              message={message.text}
              onRetry={() => void ask(message.retryPrompt)}
            />
          );
        })}

        {loading && <TypingIndicator />}
        <div ref={threadEndRef} className={styles.threadEnd} />
      </div>
    </Panel>
  );
}
