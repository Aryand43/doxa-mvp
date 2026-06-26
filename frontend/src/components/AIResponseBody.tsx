import type { AIResponse } from "../app/types";
import { MetricStrip } from "./MetricStrip";
import { MetricChart } from "./MetricChart";
import { DataTable } from "./DataTable";
import { AlertList } from "./AlertList";
import styles from "./AIResponseBody.module.css";

export type OutputMode = "summary" | "table" | "chart";

type AIResponseBodyProps = {
  data: AIResponse;
  variant?: "card" | "chat";
  outputMode?: OutputMode;
};

export function AIResponseBody({
  data,
  variant = "card",
  outputMode = "summary",
}: AIResponseBodyProps) {
  const confidencePct = Math.round(data.confidence * 100);
  const showSummary = outputMode === "summary";
  const showTable = outputMode === "table" && data.table;
  const showChart = outputMode === "chart" && data.metrics.length > 0;

  return (
    <div className={variant === "chat" ? styles.chatBody : styles.cardBody}>
      {showSummary && (
        <>
          {data.metrics.length > 0 && <MetricStrip metrics={data.metrics} />}
          {data.narrative && <p className={styles.narrative}>{data.narrative}</p>}
          {data.bullets.length > 0 && (
            <ul className={styles.bullets}>
              {data.bullets.map((bullet, index) => (
                <li key={index}>{bullet}</li>
              ))}
            </ul>
          )}
          {data.table && (
            <div className={styles.tableWrap}>
              <DataTable table={data.table} />
            </div>
          )}
        </>
      )}

      {showTable && data.table && (
        <div className={styles.tableWrap}>
          <DataTable table={data.table} />
        </div>
      )}

      {showChart && <MetricChart metrics={data.metrics} />}

      {showSummary && <AlertList alerts={data.alerts} />}

      {showSummary && data.evidence.length > 0 && (
        <details className={styles.evidence}>
          <summary className={styles.evidenceSummary}>
            Evidence · {data.evidence.length} records
          </summary>
          <ul className={styles.evidenceList}>
            {data.evidence.map((item, index) => (
              <li key={index} className={styles.evidenceItem}>
                <span className={styles.evidenceSource}>{item.source}</span>
                {item.doc_id && <span className={styles.evidenceId}>{item.doc_id}</span>}
                {item.score != null && (
                  <span className={styles.evidenceScore}>score {item.score.toFixed(2)}</span>
                )}
                <p className={styles.evidenceSnippet}>{item.snippet}</p>
              </li>
            ))}
          </ul>
        </details>
      )}

      {showSummary && data.actions.length > 0 && (
        <div className={styles.actions}>
          {data.actions.map((action, index) => (
            <button
              key={index}
              type="button"
              className={action.kind === "primary" ? undefined : "btn-secondary"}
              title={action.hint ?? undefined}
              disabled
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      <footer className={styles.footer}>
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
      </footer>
    </div>
  );
}
