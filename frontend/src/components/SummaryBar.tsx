import { useEffect, useState } from "react";
import { fetchSummary, type DemoResponse } from "../lib/api";

export function SummaryBar() {
  const [summary, setSummary] = useState<DemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchSummary()
      .then((data) => active && setSummary(data))
      .catch((err) =>
        active && setError(err instanceof Error ? err.message : "Failed to load summary."),
      );
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return <div className="summary-bar summary-bar-error">Snapshot unavailable — {error}</div>;
  }

  if (!summary) {
    return <div className="summary-bar summary-bar-loading">Loading snapshot…</div>;
  }

  return (
    <div className="summary-bar">
      {summary.metrics.map((m, i) => (
        <div key={i} className="summary-kpi">
          <span className="summary-kpi-value">{m.value}</span>
          <span className="summary-kpi-label">{m.label}</span>
        </div>
      ))}
    </div>
  );
}
