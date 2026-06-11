import type { AlertItem } from "../app/types";

function severityClass(severity: string): string {
  const s = severity.toLowerCase();
  if (s === "high") return "sev-high";
  if (s === "medium") return "sev-medium";
  return "sev-low";
}

export function AlertList({ alerts }: { alerts: AlertItem[] }) {
  if (alerts.length === 0) return null;
  return (
    <ul className="alert-list">
      {alerts.map((a) => (
        <li key={a.id} className={`alert-item ${severityClass(a.severity)}`}>
          <div className="alert-head">
            <span className={`sev-badge ${severityClass(a.severity)}`}>
              {a.severity.toUpperCase()}
            </span>
            <span className="alert-type">{a.type.replace(/_/g, " ")}</span>
            <span className="alert-source">{a.source}</span>
          </div>
          <p className="alert-title">{a.title}</p>
          {a.description && <p className="alert-desc">{a.description}</p>}
          {a.records.length > 0 && (
            <p className="alert-records">
              Records: {a.records.slice(0, 6).join(", ")}
            </p>
          )}
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
