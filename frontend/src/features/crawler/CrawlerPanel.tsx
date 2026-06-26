import { useCallback, useEffect, useState } from "react";
import { runCrawl } from "../../app/api";
import { isForbiddenError } from "../../app/auth";
import type { CrawlResponse, Metric } from "../../app/types";
import type { ReviewDisposition } from "../../components/AlertReviewActions";
import { Panel } from "../../components/Panel";
import { MetricStrip } from "../../components/MetricStrip";
import { AlertList } from "../../components/AlertList";
import { ScanProcessing } from "../../components/ScanProcessing";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import styles from "./CrawlerPanel.module.css";

const PROCESSING_STEPS = 7;

function statsToMetrics(scan: CrawlResponse["scan_stats"]): Metric[] {
  return [
    { label: "Records scanned", value: scan.records_scanned.toLocaleString() },
    { label: "Alerts", value: String(scan.alerts_found) },
    { label: "High severity", value: String(scan.by_severity.high ?? 0) },
    { label: "Index", value: scan.retrieval_backend === "iris" ? "IRIS" : "Local" },
  ];
}

export function CrawlerPanel() {
  const [result, setResult] = useState<CrawlResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [dispositions, setDispositions] = useState<Record<string, ReviewDisposition>>({});
  const [showReviewed, setShowReviewed] = useState(false);

  const scan = useCallback(async () => {
    setError(null);
    setForbidden(false);
    setLoading(true);
    setActiveStep(0);
    try {
      const response = await runCrawl(60, true);
      setResult(response);
      setDispositions({});
    } catch (err) {
      setForbidden(isForbiddenError(err));
      setError(err instanceof Error ? err.message : "The scan did not complete.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!loading) return;
    const timer = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, PROCESSING_STEPS - 1));
    }, 420);
    return () => window.clearInterval(timer);
  }, [loading]);

  const alerts =
    result?.alerts.filter((alert) =>
      showReviewed ? true : !dispositions[alert.id],
    ) ?? [];

  return (
    <Panel
      kicker="Scan"
      title="AI Data Crawler"
      description="Deterministic detectors plus vector retrieval — surfaces risk across invoices, vendors, and contracts."
      controls={
        <div className={styles.toolbar}>
          <button type="button" onClick={() => void scan()} disabled={loading}>
            {loading ? "Scanning…" : result ? "Run scan again" : "Run scan"}
          </button>
          {result && (
            <label className={styles.filter}>
              <input
                type="checkbox"
                checked={showReviewed}
                onChange={(event) => setShowReviewed(event.target.checked)}
              />
              Show reviewed alerts
            </label>
          )}
        </div>
      }
    >
      {loading && <ScanProcessing activeIndex={activeStep} />}
      {error && (
        <ErrorState
          title={forbidden ? "Access denied" : "The scan couldn't run."}
          message={error}
          onRetry={forbidden ? undefined : () => void scan()}
        />
      )}
      {!loading && !error && !result && (
        <EmptyState
          title="Run a dataset scan"
          message="Start a crawl to surface procurement alerts. Scans are tenant-scoped and require CRAWLER:read."
        />
      )}
      {result && !loading && (
        <>
          <ScanProcessing phases={result.phases} activeIndex={result.phases.length} complete />
          <MetricStrip metrics={statsToMetrics(result.scan_stats)} />
          <p className={styles.digest}>{result.digest}</p>
          <AlertList
            alerts={alerts}
            reviewable
            dispositions={dispositions}
            onReview={(alertId, disposition) =>
              setDispositions((current) => ({ ...current, [alertId]: disposition }))
            }
          />
          {alerts.length === 0 && (
            <p className={styles.emptyAlerts}>
              {showReviewed
                ? "No alerts in this scan."
                : "All alerts reviewed — enable “Show reviewed alerts” to see them."}
            </p>
          )}
        </>
      )}
    </Panel>
  );
}
