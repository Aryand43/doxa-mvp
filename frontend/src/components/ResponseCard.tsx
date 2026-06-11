import type { AIResponse } from "../app/types";
import { MetricStrip } from "./MetricStrip";
import { DataTable } from "./DataTable";
import { AlertList } from "./AlertList";

export function ResponseCard({ data }: { data: AIResponse }) {
  return (
    <div className="response-card">
      <div className="response-head">
        <h3 className="response-title">{data.title}</h3>
        <span className="response-tag">{data.mode}</span>
      </div>

      <MetricStrip metrics={data.metrics} />

      {data.narrative && <p className="response-narrative">{data.narrative}</p>}

      {data.bullets.length > 0 && (
        <ul className="response-bullets">
          {data.bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      )}

      {data.table && <DataTable table={data.table} />}

      <AlertList alerts={data.alerts} />

      {data.evidence.length > 0 && (
        <details className="evidence">
          <summary>Evidence ({data.evidence.length})</summary>
          <ul className="evidence-list">
            {data.evidence.map((e, i) => (
              <li key={i} className="evidence-item">
                <span className="evidence-source">{e.source}</span>
                <span className="evidence-snippet">{e.snippet}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {data.actions.length > 0 && (
        <div className="response-actions">
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

      <div className="response-footer">
        {data.data_scope.length > 0 && (
          <span>scope: {data.data_scope.join(", ")}</span>
        )}
        <span>confidence {Math.round(data.confidence * 100)}%</span>
      </div>
    </div>
  );
}
