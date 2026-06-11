import { useState } from "react";
import { Card } from "../../components/Card";
import { ResponseView } from "../../components/ResponseView";
import {
  generateDemoReport,
  REPORT_TYPES,
  type DemoResponse,
} from "../../lib/api";

const TARGET_HINTS: Record<string, string> = {
  spend_analysis: "Project code (optional, e.g. SI-2422)",
  vendor_performance: "Vendor name (e.g. GreenBuild)",
  entity_summary: "Entity name (optional)",
  on_demand: "Describe the report you want",
};

export function ReportPanel() {
  const [selected, setSelected] = useState<string>(REPORT_TYPES[0].id);
  const [target, setTarget] = useState("");
  const [report, setReport] = useState<DemoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (loading) return;
    setError(null);
    setReport(null);
    setLoading(true);

    try {
      const text = target.trim();
      const data =
        selected === "on_demand"
          ? await generateDemoReport(selected, undefined, text || "procurement overview")
          : await generateDemoReport(selected, text || undefined);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate report.");
    } finally {
      setLoading(false);
    }
  }

  const hint = TARGET_HINTS[selected];

  return (
    <Card title="AI Reports">
      <div className="report-types">
        {REPORT_TYPES.map((rt) => (
          <button
            key={rt.id}
            type="button"
            className={`chip ${selected === rt.id ? "chip-active" : ""}`}
            onClick={() => setSelected(rt.id)}
            disabled={loading}
          >
            {rt.label}
          </button>
        ))}
      </div>

      {hint && (
        <input
          type="text"
          className="report-prompt"
          placeholder={hint}
          aria-label="Report target"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          disabled={loading}
        />
      )}

      <button type="button" onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating…" : "Generate report"}
      </button>

      <div className="report-output">
        {error && <p className="chat-error">{error}</p>}
        {report && !loading && <ResponseView data={report} />}
        {!report && !loading && !error && (
          <p className="placeholder">
            Pick a report type and generate a structured report card.
          </p>
        )}
      </div>
    </Card>
  );
}
