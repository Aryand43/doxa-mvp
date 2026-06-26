import type { AIResponse } from "../app/types";
import { AIResponseBody, type OutputMode } from "./AIResponseBody";
import styles from "./ResponseCard.module.css";

export function ResponseCard({
  data,
  outputMode = "summary",
  compact = false,
}: {
  data: AIResponse;
  outputMode?: OutputMode;
  compact?: boolean;
}) {
  return (
    <article className={compact ? `${styles.card} ${styles.cardCompact}` : styles.card}>
      {!compact && (
        <div className={styles.head}>
          <h3 className={styles.title}>{data.title}</h3>
          <span className={styles.mode}>{data.mode}</span>
        </div>
      )}
      <AIResponseBody data={data} variant="card" outputMode={outputMode} />
    </article>
  );
}
