import type { Metric } from "../app/types";
import styles from "./MetricStrip.module.css";

/**
 * Figures presented as a financial ledger line.
 *  - "tape"   : the masthead hero — large mono figures split by hairlines.
 *  - "inline" : compact cards used inside response cards and the crawler.
 *  - "dense"  : hairline-separated row for chat / analyst summaries.
 */
export function MetricStrip({
  metrics,
  variant = "inline",
}: {
  metrics: Metric[];
  variant?: "tape" | "inline" | "dense";
}) {
  if (metrics.length === 0) return null;

  if (variant === "tape") {
    return (
      <dl className={styles.tape}>
        {metrics.map((m, i) => (
          <div key={i} className={styles.tapeItem}>
            <dd className={styles.tapeValue}>{m.value}</dd>
            <dt className={styles.tapeLabel}>{m.label}</dt>
          </div>
        ))}
      </dl>
    );
  }

  if (variant === "dense") {
    return (
      <dl className={styles.dense}>
        {metrics.map((m, i) => (
          <div key={i} className={styles.denseItem}>
            <dt className={styles.denseLabel}>{m.label}</dt>
            <dd className={styles.denseValue}>{m.value}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return (
    <dl className={styles.strip}>
      {metrics.map((m, i) => (
        <div key={i} className={styles.metric}>
          <dd className={styles.value}>{m.value}</dd>
          <dt className={styles.label}>{m.label}</dt>
          {m.hint && <dd className={styles.hint}>{m.hint}</dd>}
        </div>
      ))}
    </dl>
  );
}
