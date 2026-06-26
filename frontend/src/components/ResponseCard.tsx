import type { AIResponse } from "../app/types";
import { AIResponseBody, type OutputMode } from "./AIResponseBody";
import styles from "./ResponseCard.module.css";

export function ResponseCard({
  data,
  outputMode = "summary",
}: {
  data: AIResponse;
  outputMode?: OutputMode;
}) {
  return (
    <article className={styles.card}>
      <div className={styles.head}>
        <h3 className={styles.title}>{data.title}</h3>
        <span className={styles.mode}>{data.mode}</span>
      </div>
      <AIResponseBody data={data} variant="card" outputMode={outputMode} />
    </article>
  );
}
