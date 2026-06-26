import type { AIResponse } from "../../app/types";
import { MetricStrip } from "../../components/MetricStrip";
import { DataTable } from "../../components/DataTable";
import { AlertList } from "../../components/AlertList";
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
  const confidencePct = Math.round(data.confidence * 100);

  return (
    <div className={styles.rowAssistant}>
      <div className={styles.avatar} aria-hidden>
        AI
      </div>
      <div className={styles.assistantBubble}>
        <div className={styles.assistantHead}>
          <span className={styles.assistantLabel}>Assistant</span>
          {data.title && <span className={styles.assistantTopic}>{data.title}</span>}
        </div>

        {data.narrative && <p className={styles.narrative}>{data.narrative}</p>}

        {data.bullets.length > 0 && (
          <ul className={styles.bullets}>
            {data.bullets.map((bullet, index) => (
              <li key={index}>{bullet}</li>
            ))}
          </ul>
        )}

        {data.metrics.length > 0 && (
          <div className={styles.metrics}>
            <MetricStrip metrics={data.metrics} />
          </div>
        )}

        {data.table && (
          <div className={styles.tableWrap}>
            <DataTable table={data.table} />
          </div>
        )}

        <AlertList alerts={data.alerts} />

        {data.evidence.length > 0 && (
          <details className={styles.evidence}>
            <summary>Evidence · {data.evidence.length} records</summary>
            <ul>
              {data.evidence.map((item, index) => (
                <li key={index}>
                  <span className={styles.evidenceSource}>{item.source}</span>
                  {item.doc_id && <span className={styles.evidenceId}>{item.doc_id}</span>}
                  <p className={styles.evidenceSnippet}>{item.snippet}</p>
                </li>
              ))}
            </ul>
          </details>
        )}

        {data.actions.length > 0 && (
          <div className={styles.actions}>
            {data.actions.map((action, index) => (
              <button
                key={index}
                type="button"
                className={action.kind === "primary" ? undefined : "btn-secondary"}
                title={action.hint ?? undefined}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}

        <footer className={styles.meta}>
          {data.data_scope.length > 0 && (
            <span className={styles.scope}>{data.data_scope.join(" · ")}</span>
          )}
          <span className={styles.confidence}>{confidencePct}% confidence</span>
        </footer>
      </div>
    </div>
  );
}

export function ErrorMessage({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className={styles.rowAssistant}>
      <div className={`${styles.avatar} ${styles.avatarError}`} aria-hidden>
        !
      </div>
      <div className={`${styles.assistantBubble} ${styles.errorBubble}`}>
        <p className={styles.errorTitle}>Couldn&apos;t get an answer</p>
        <p className={styles.errorText}>{message}</p>
        {onRetry && (
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
