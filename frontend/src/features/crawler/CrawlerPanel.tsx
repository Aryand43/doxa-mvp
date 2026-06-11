import { useCallback, useEffect, useState } from "react";
import { runCrawl } from "../../app/api";
import type { CrawlResponse, Metric } from "../../app/types";
import { MetricStrip } from "../../components/MetricStrip";
import { AlertList } from "../../components/AlertList";
import { LoadingState } from "../../components/LoadingState";
import { ErrorState } from "../../components/ErrorState";

function statsToMetrics(scan: CrawlResponse["scan_stats"]): Metric[] {
  return [
    { label: "Records scanned", value: scan.records_scanned.toLocaleString() },
    { label: "Alerts", value: String(scan.alerts_found) },
    { label: "High severity", value: String(scan.by_severity.high ?? 0) },
    { label: "Retrieval", value: scan.retrieval_backend },
  ];
}

export function CrawlerPanel() {
  const [result, setResult] = useState<CrawlResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scan = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setResult(await runCrawl());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run scan.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void scan();
  }, [scan]);

  return (
    <section className="panel">
      <header className="panel-header">
        <h2>AI Data Crawler</h2>
        <p>Vector-grounded anomaly scan over procurement data.</p>
      </header>

      <div className="panel-toolbar">
        <button type="button" onClick={() => void scan()} disabled={loading}>
          {loading ? "Scanning…" : "Run scan"}
        </button>
      </div>

      <div className="panel-output">
        {loading && !result && <LoadingState label="Scanning data sources…" />}
        {error && <ErrorState message={error} />}
        {result && (
          <>
            <MetricStrip metrics={statsToMetrics(result.scan_stats)} />
            <p className="response-narrative">{result.digest}</p>
            <AlertList alerts={result.alerts} />
          </>
        )}
      </div>
    </section>
  );
}
