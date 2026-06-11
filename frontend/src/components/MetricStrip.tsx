import type { Metric } from "../app/types";

export function MetricStrip({ metrics }: { metrics: Metric[] }) {
  if (metrics.length === 0) return null;
  return (
    <div className="metric-strip">
      {metrics.map((m, i) => (
        <div key={i} className="metric">
          <span className="metric-value">{m.value}</span>
          <span className="metric-label">{m.label}</span>
          {m.hint && <span className="metric-hint">{m.hint}</span>}
        </div>
      ))}
    </div>
  );
}
