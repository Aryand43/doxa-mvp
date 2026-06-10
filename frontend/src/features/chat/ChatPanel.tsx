import { useState, type FormEvent } from "react";
import { Card } from "../../components/Card";
import { sendChatMessage } from "../../lib/api";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const { reply } = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="AI Assistant">
      <div className="chat-panel">
        <div className="chat-messages">
          {messages.length === 0 && !loading ? (
            <p className="placeholder">Start a conversation with the AI assistant.</p>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`chat-message chat-message-${msg.role}`}>
                {msg.content}
              </div>
            ))
          )}
          {loading && <p className="placeholder">Thinking…</p>}
          {error && <p className="chat-error">{error}</p>}
        </div>
        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask something…"
            aria-label="Message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || input.trim() === ""}>
            Send
          </button>
        </form>
      </div>
    </Card>
  );
}
