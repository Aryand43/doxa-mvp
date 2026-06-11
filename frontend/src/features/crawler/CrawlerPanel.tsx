import { useCallback, useEffect, useState } from "react";
import { runCrawl } from "../../app/api";
import type { CrawlResponse, Metric } from "../../app/types";
import { Panel } from "../../components/Panel";
import { MetricStrip } from "../../components/MetricStrip";
import { AlertList } from "../../components/AlertList";
import { ScanProcessing } from "../../components/ScanProcessing";
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
  const [activeStep, setActiveStep] = useState(0);

  const scan = useCallback(async () => {
    setError(null);
    setLoading(true);
    setActiveStep(0);
    try {
      setResult(await runCrawl(60, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "The scan did not complete.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void scan();
  }, [scan]);

  useEffect(() => {
    if (!loading) return;
    const timer = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, PROCESSING_STEPS - 1));
    }, 420);
    return () => window.clearInterval(timer);
  }, [loading]);

  return (
    <Panel
      kicker="Scan"
      title="AI Data Crawler"
      description="Deterministic detectors plus vector retrieval — surfaces risk across invoices, vendors, and contracts."
      controls={
        <div className={styles.toolbar}>
          <button type="button" onClick={() => void scan()} disabled={loading}>
            {loading ? "Scanning…" : "Run scan"}
          </button>
        </div>
      }
    >
      {loading && <ScanProcessing activeIndex={activeStep} />}
      {error && <ErrorState title="The scan couldn't run." message={error} onRetry={() => void scan()} />}
      {result && !loading && (
        <>
          <ScanProcessing phases={result.phases} activeIndex={result.phases.length} complete />
          <MetricStrip metrics={statsToMetrics(result.scan_stats)} />
          <p className={styles.digest}>{result.digest}</p>
          <AlertList alerts={result.alerts} />
        </>
      )}
    </Panel>
  );
}
