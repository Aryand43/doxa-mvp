import { useCallback, useEffect, useState } from "react";
import { Card } from "../../components/Card";
import { ResponseView } from "../../components/ResponseView";
import { fetchAlerts, type DemoResponse } from "../../lib/api";

export function AlertsPanel() {
  const [digest, setDigest] = useState<DemoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await fetchAlerts(12);
      setDigest(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Card title="AI Data Crawler">
      <div className="crawler-toolbar">
        <button type="button" onClick={() => void load()} disabled={loading}>
          {loading ? "Scanning…" : "Run scan"}
        </button>
      </div>

      <div className="crawler-output">
        {loading && !digest && <p className="placeholder">Scanning data sources…</p>}
        {error && <p className="chat-error">{error}</p>}
        {digest && <ResponseView data={digest} />}
      </div>
    </Card>
  );
}
