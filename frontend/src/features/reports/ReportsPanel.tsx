import { useEffect, useState } from "react";
import { fetchReportTypes, generateReport } from "../../app/api";
import type { AIResponse, ReportType } from "../../app/types";
import { Panel } from "../../components/Panel";
import { ResponseCard } from "../../components/ResponseCard";
import { LoadingState } from "../../components/LoadingState";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import styles from "./ReportsPanel.module.css";

const TARGET_HINTS: Record<string, string> = {
  spend_analysis: "Project code — optional (e.g. SI-2422)",
  vendor_performance: "Vendor name (e.g. GreenBuild)",
  entity_summary: "Entity name — optional",
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
      setError(err instanceof Error ? err.message : "The report could not be built.");
    } finally {
      setLoading(false);
    }
  }

  const hint = TARGET_HINTS[selected];

  return (
    <Panel
      kicker="Generate"
      title="AI Reports"
      description="Structured, grounded summaries — built on demand from the same data."
      controls={
        <>
          <div className={styles.segmented} role="group" aria-label="Report type">
            {types.map((rt) => (
              <button
                key={rt.id}
                type="button"
                className={`${styles.segment} ${selected === rt.id ? styles.segmentOn : ""}`}
                aria-pressed={selected === rt.id}
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
        </>
      }
    >
      {loading && <LoadingState label="Building report" />}
      {error && (
        <ErrorState title="The report couldn't be built." message={error} onRetry={generate} />
      )}
      {report && !loading && <ResponseCard data={report} />}
      {!report && !loading && !error && (
        <EmptyState
          title="Generate a grounded report."
          message="Choose a report type, add a target if you have one, then generate."
        />
      )}
    </Panel>
  );
}
