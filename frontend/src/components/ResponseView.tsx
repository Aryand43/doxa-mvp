import type {
  AlertItem,
  DemoResponse,
  EvidenceItem,
  Metric,
  TableData,
} from "../lib/api";

function severityClass(severity: string): string {
  const s = severity.toLowerCase();
  if (s === "high") return "sev-high";
  if (s === "medium") return "sev-medium";
  return "sev-low";
}

function MetricsGrid({ metrics }: { metrics: Metric[] }) {
  if (metrics.length === 0) return null;
  return (
    <div className="metrics-grid">
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

function Table({ table }: { table: TableData }) {
  if (!table.columns.length) return null;
  return (
    <div className="rv-table-wrap">
      <table className="rv-table">
        <thead>
          <tr>
            {table.columns.map((c, i) => (
              <th key={i}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci}>{cell === null || cell === "" ? "—" : String(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Alerts({ alerts }: { alerts: AlertItem[] }) {
  if (alerts.length === 0) return null;
  return (
    <ul className="alert-list">
      {alerts.map((a) => (
        <li key={a.id} className={`alert-item ${severityClass(a.severity)}`}>
          <div className="alert-meta">
            <span className={`sev-badge ${severityClass(a.severity)}`}>
              {a.severity.toUpperCase()}
            </span>
            <span className="alert-source">{a.source}</span>
          </div>
          <p className="alert-title">{a.title}</p>
          {a.description && <p className="alert-message">{a.description}</p>}
          {a.recommended_action && (
            <p className="alert-action">
              <span className="alert-action-label">Recommended:</span>{" "}
              {a.recommended_action}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

function Evidence({ evidence }: { evidence: EvidenceItem[] }) {
  if (evidence.length === 0) return null;
  return (
    <details className="evidence">
      <summary>Evidence ({evidence.length})</summary>
      <ul className="evidence-list">
        {evidence.map((e, i) => (
          <li key={i} className="evidence-item">
            <span className="evidence-source">{e.source}</span>
            <span className="evidence-snippet">{e.snippet}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function ResponseView({ data }: { data: DemoResponse }) {
  return (
    <div className="response-view">
      <div className="rv-head">
        <h3 className="rv-title">{data.title}</h3>
        <span className="rv-intent">{data.intent}</span>
      </div>

      <MetricsGrid metrics={data.metrics} />

      {data.narrative && <p className="rv-narrative">{data.narrative}</p>}

      {data.bullets.length > 0 && (
        <ul className="rv-bullets">
          {data.bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      )}

      {data.table && <Table table={data.table} />}

      <Alerts alerts={data.alerts} />

      <Evidence evidence={data.evidence} />

      {data.actions.length > 0 && (
        <div className="rv-actions">
          {data.actions.map((a, i) => (
            <button
              key={i}
              type="button"
              className={a.kind === "primary" ? "" : "btn-secondary"}
              title={a.hint ?? undefined}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}

      {(data.data_scope.length > 0 || data.confidence) && (
        <div className="rv-footer">
          {data.data_scope.length > 0 && (
            <span className="rv-scope">scope: {data.data_scope.join(", ")}</span>
          )}
          <span className="rv-confidence">
            confidence {Math.round(data.confidence * 100)}%
          </span>
        </div>
      )}
    </div>
  );
}
