import type { AIResponse } from "../../app/types";
import { AIResponseBody } from "../../components/AIResponseBody";
import styles from "./ChatMessage.module.css";

export function UserMessage({ text }: { text: string }) {
  return (
    <div className={styles.rowUser}>
      <div className={styles.userBubble}>
        <p className={styles.userText}>{text}</p>
      </div>
    </div>
  );
}

export function AssistantMessage({ data }: { data: AIResponse }) {
  return (
    <div className={styles.rowAssistant}>
      <div className={styles.avatar} aria-hidden>
        AI
      </div>
      <div className={styles.assistantBubble}>
        <div className={styles.assistantHead}>
          <span className={styles.assistantLabel}>Assistant</span>
          {data.title && <span className={styles.assistantTopic}>{data.title}</span>}
          <span className={styles.groundedBadge}>Grounded</span>
        </div>
        <AIResponseBody data={data} variant="chat" />
      </div>
    </div>
  );
}

export function ErrorMessage({
  message,
  onRetry,
  forbidden,
}: {
  message: string;
  onRetry?: () => void;
  forbidden?: boolean;
}) {
  return (
    <div className={styles.rowAssistant}>
      <div className={`${styles.avatar} ${styles.avatarError}`} aria-hidden>
        !
      </div>
      <div className={`${styles.assistantBubble} ${styles.errorBubble}`}>
        <p className={styles.errorTitle}>
          {forbidden ? "Access denied" : "Couldn&apos;t get an answer"}
        </p>
        <p className={styles.errorText}>{message}</p>
        {onRetry && !forbidden && (
          <button type="button" className="btn-secondary" onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className={styles.rowAssistant} aria-live="polite" aria-label="Assistant is thinking">
      <div className={styles.avatar} aria-hidden>
        AI
      </div>
      <div className={`${styles.assistantBubble} ${styles.typingBubble}`}>
        <span className={styles.typingDots}>
          <span />
          <span />
          <span />
        </span>
      </div>
    </div>
  );
}
