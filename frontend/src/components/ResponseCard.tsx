import type { AIResponse } from "../app/types";
import { MetricStrip } from "./MetricStrip";
import { DataTable } from "./DataTable";
import { AlertList } from "./AlertList";
import styles from "./ResponseCard.module.css";

export function ResponseCard({ data }: { data: AIResponse }) {
  const confidencePct = Math.round(data.confidence * 100);
  return (
    <article className={styles.card}>
      <div className={styles.head}>
        <h3 className={styles.title}>{data.title}</h3>
        <span className={styles.mode}>{data.mode}</span>
      </div>

      <MetricStrip metrics={data.metrics} />

      {data.narrative && <p className={styles.narrative}>{data.narrative}</p>}

      {data.bullets.length > 0 && (
        <ul className={styles.bullets}>
          {data.bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      )}

      {data.table && <DataTable table={data.table} />}

      <AlertList alerts={data.alerts} />

      {data.evidence.length > 0 && (
        <details className={styles.evidence}>
          <summary className={styles.evidenceSummary}>
            Evidence · {data.evidence.length} records
          </summary>
          <ul className={styles.evidenceList}>
            {data.evidence.map((e, i) => (
              <li key={i} className={styles.evidenceItem}>
                <span className={styles.evidenceSource}>{e.source}</span>
                <span className={styles.evidenceSnippet}>{e.snippet}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {data.actions.length > 0 && (
        <div className={styles.actions}>
          {data.actions.map((a, i) => (
            <button
              key={i}
              type="button"
              className={a.kind === "primary" ? undefined : "btn-secondary"}
              title={a.hint ?? undefined}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}

      <div className={styles.footer}>
        {data.data_scope.length > 0 && (
          <span className={styles.scope}>scope · {data.data_scope.join(", ")}</span>
        )}
        <span
          className={styles.confidence}
          role="img"
          aria-label={`Confidence ${confidencePct} percent`}
        >
          <span className={styles.confidenceLabel}>Confidence</span>
          <span className={styles.confidenceTrack} aria-hidden>
            <span className={styles.confidenceFill} style={{ width: `${confidencePct}%` }} />
          </span>
          <span className={styles.confidenceValue}>{confidencePct}%</span>
        </span>
      </div>
    </article>
  );
}
