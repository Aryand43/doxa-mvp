import { useEffect, useState } from "react";
import { fetchReportTypes, generateReport } from "../../app/api";
import { isForbiddenError } from "../../app/auth";
import type { AIResponse, ReportType } from "../../app/types";
import { downloadCsv, tableToCsv } from "../../lib/exportTable";
import { Panel } from "../../components/Panel";
import { ResponseCard } from "../../components/ResponseCard";
import { OutputToolbar } from "../../components/OutputToolbar";
import type { OutputMode } from "../../components/AIResponseBody";
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

type ReportRun = {
  id: string;
  label: string;
  response: AIResponse;
};

export function ReportsPanel() {
  const [types, setTypes] = useState<ReportType[]>([]);
  const [selected, setSelected] = useState<string>("spend_analysis");
  const [target, setTarget] = useState("");
  const [refinePrompt, setRefinePrompt] = useState("");
  const [runs, setRuns] = useState<ReportRun[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [outputMode, setOutputMode] = useState<OutputMode>("summary");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    fetchReportTypes()
      .then((rt) => {
        setTypes(rt);
        if (rt.length) setSelected(rt[0].id);
      })
      .catch((err) => {
        setTypes([]);
        if (isForbiddenError(err)) {
          setForbidden(true);
          setError(err instanceof Error ? err.message : "Access denied.");
        }
      });
  }, []);

  const activeRun = runs.find((run) => run.id === activeRunId) ?? runs[runs.length - 1] ?? null;
  const report = activeRun?.response ?? null;

  async function generate(refinement?: string) {
    if (loading) return;
    setError(null);
    setForbidden(false);
    setLoading(true);
    try {
      const text = target.trim();
      const refine = refinement?.trim();
      const data =
        selected === "on_demand"
          ? await generateReport(
              selected,
              undefined,
              refine || text || "procurement overview",
            )
          : refine
            ? await generateReport(selected, text || undefined, refine)
            : await generateReport(selected, text || undefined);
      const label = types.find((type) => type.id === selected)?.label ?? selected;
      const run: ReportRun = {
        id: `${Date.now()}`,
        label: refine ? `${label} · refinement` : label,
        response: data,
      };
      setRuns((current) => [...current, run]);
      setActiveRunId(run.id);
      setOutputMode("summary");
      if (refine) setRefinePrompt("");
    } catch (err) {
      setForbidden(isForbiddenError(err));
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
          <button type="button" onClick={() => void generate()} disabled={loading}>
            {loading ? "Generating…" : "Generate report"}
          </button>
        </>
      }
    >
      {loading && <LoadingState label="Building report" />}
      {error && (
        <ErrorState
          title={forbidden ? "Access denied" : "The report couldn't be built."}
          message={error}
          onRetry={forbidden ? undefined : () => void generate()}
        />
      )}

      {report && !loading && (
        <>
          {runs.length > 1 && (
            <div className={styles.history} role="group" aria-label="Report iterations">
              {runs.map((run) => (
                <button
                  key={run.id}
                  type="button"
                  className={`${styles.historyItem} ${run.id === activeRun?.id ? styles.historyOn : ""}`}
                  aria-pressed={run.id === activeRun?.id}
                  onClick={() => setActiveRunId(run.id)}
                >
                  {run.label}
                </button>
              ))}
            </div>
          )}

          <OutputToolbar
            mode={outputMode}
            onModeChange={setOutputMode}
            hasTable={Boolean(report.table?.columns.length)}
            hasMetrics={report.metrics.length > 0}
            onExport={
              report.table
                ? () =>
                    downloadCsv(
                      `${report.title.replace(/\s+/g, "-").toLowerCase()}.csv`,
                      tableToCsv(report.table!),
                    )
                : undefined
            }
          />

          <ResponseCard data={report} outputMode={outputMode} />

          <form
            className={styles.refine}
            onSubmit={(event) => {
              event.preventDefault();
              void generate(refinePrompt);
            }}
          >
            <input
              type="text"
              placeholder="Refine this report (e.g. focus on high-risk vendors only)"
              aria-label="Refinement prompt"
              value={refinePrompt}
              onChange={(event) => setRefinePrompt(event.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading || refinePrompt.trim() === ""}>
              Refine
            </button>
          </form>
        </>
      )}

      {!report && !loading && !error && (
        <EmptyState
          title="Generate a grounded report."
          message="Choose a report type, add a target if you have one, then generate."
        />
      )}
    </Panel>
  );
}
