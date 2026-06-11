import { useEffect, useState } from "react";
import { fetchReportTypes, generateReport } from "../../app/api";
import type { AIResponse, ReportType } from "../../app/types";
import { ResponseCard } from "../../components/ResponseCard";
import { LoadingState } from "../../components/LoadingState";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";

const TARGET_HINTS: Record<string, string> = {
  spend_analysis: "Project code (optional, e.g. SI-2422)",
  vendor_performance: "Vendor name (e.g. GreenBuild)",
  entity_summary: "Entity name (optional)",
  on_demand: "Describe the report you want",
};

export function ReportsPanel() {
  const [types, setTypes] = useState<ReportType[]>([]);
  const [selected, setSelected] = useState<string>("spend_analysis");
  const [target, setTarget] = useState("");
  const [report, setReport] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReportTypes()
      .then((rt) => {
        setTypes(rt);
        if (rt.length) setSelected(rt[0].id);
      })
      .catch(() => setTypes([]));
  }, []);

  async function generate() {
    if (loading) return;
    setError(null);
    setReport(null);
    setLoading(true);
    try {
      const text = target.trim();
      const data =
        selected === "on_demand"
          ? await generateReport(selected, undefined, text || "procurement overview")
          : await generateReport(selected, text || undefined);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate report.");
    } finally {
      setLoading(false);
    }
  }

  const hint = TARGET_HINTS[selected];

  return (
    <section className="panel">
      <header className="panel-header">
        <h2>AI Reports</h2>
        <p>Grounded reports, generated on demand.</p>
      </header>

      <div className="chip-row">
        {types.map((rt) => (
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
          className="text-input"
          placeholder={hint}
          aria-label="Report target"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          disabled={loading}
        />
      )}

      <button type="button" onClick={generate} disabled={loading}>
        {loading ? "Generating…" : "Generate report"}
      </button>

      <div className="panel-output">
        {loading && <LoadingState label="Building report…" />}
        {error && <ErrorState message={error} />}
        {report && !loading && <ResponseCard data={report} />}
        {!report && !loading && !error && (
          <EmptyState message="Pick a report type and generate a structured report." />
        )}
      </div>
    </section>
  );
}
