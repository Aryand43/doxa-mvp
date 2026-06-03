import { Card } from "../../components/Card";

const SAMPLE_REPORTS = [
  { id: "1", title: "Weekly summary", status: "Draft" },
  { id: "2", title: "Market overview", status: "Ready" },
];

export function ReportPanel() {
  return (
    <Card title="AI Reports">
      <ul className="report-list">
        {SAMPLE_REPORTS.map((report) => (
          <li key={report.id} className="report-item">
            <span className="report-title">{report.title}</span>
            <span className="report-status">{report.status}</span>
          </li>
        ))}
      </ul>
      <button type="button" className="btn-secondary">
        Generate report
      </button>
    </Card>
  );
}
