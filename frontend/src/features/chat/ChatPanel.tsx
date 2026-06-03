import { Card } from "../../components/Card";

export function ChatPanel() {
  return (
    <Card title="AI Assistant">
      <div className="chat-panel">
        <div className="chat-messages">
          <p className="placeholder">Start a conversation with the AI assistant.</p>
        </div>
        <form className="chat-input" onSubmit={(e) => e.preventDefault()}>
          <input type="text" placeholder="Ask something…" aria-label="Message" />
          <button type="submit">Send</button>
        </form>
      </div>
    </Card>
  );
}
