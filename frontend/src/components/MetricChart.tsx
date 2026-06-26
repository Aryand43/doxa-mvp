import type { Metric } from "../app/types";
import styles from "./MetricChart.module.css";

function numericValue(value: string): number | null {
  const parsed = Number(String(value).replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

export function MetricChart({ metrics }: { metrics: Metric[] }) {
  const rows = metrics
    .map((metric) => ({ metric, value: numericValue(metric.value) }))
    .filter((row): row is { metric: Metric; value: number } => row.value !== null);

  if (rows.length === 0) {
    return (
      <p className={styles.empty}>No numeric metrics available for chart view.</p>
    );
  }

  const max = Math.max(...rows.map((row) => row.value), 1);

  return (
    <div className={styles.chart} role="img" aria-label="Metric comparison chart">
      {rows.map(({ metric, value }) => (
        <div key={metric.label} className={styles.row}>
          <span className={styles.label}>{metric.label}</span>
          <span className={styles.track} aria-hidden>
            <span className={styles.bar} style={{ width: `${(value / max) * 100}%` }} />
          </span>
          <span className={styles.value}>{metric.value}</span>
        </div>
      ))}
    </div>
  );
}
