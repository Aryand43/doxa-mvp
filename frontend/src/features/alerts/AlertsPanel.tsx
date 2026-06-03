import { Card } from "../../components/Card";

const SAMPLE_ALERTS = [
  { id: "1", source: "SEC filings", message: "New 10-K detected for ACME Corp", time: "2m ago" },
  { id: "2", source: "News feed", message: "Earnings call transcript available", time: "15m ago" },
];

export function AlertsPanel() {
  return (
    <Card title="AI Data Crawler Alerts">
      <ul className="alert-list">
        {SAMPLE_ALERTS.map((alert) => (
          <li key={alert.id} className="alert-item">
            <div className="alert-meta">
              <span className="alert-source">{alert.source}</span>
              <span className="alert-time">{alert.time}</span>
            </div>
            <p className="alert-message">{alert.message}</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
