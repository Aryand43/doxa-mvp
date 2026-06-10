import { useState } from "react";
import { Card } from "../../components/Card";
import { generateReport } from "../../lib/api";

export function ReportPanel() {
  const [prompt, setPrompt] = useState("");
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    const text = prompt.trim();
    if (!text || loading) return;

    setError(null);
    setLoading(true);

    try {
      const result = await generateReport(text);
      setReport(result.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate report.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="AI Reports">
      <input
        type="text"
        className="report-prompt"
        placeholder="Describe the report to generate…"
        aria-label="Report prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={loading}
      />
      <button
        type="button"
        className="btn-secondary"
        onClick={handleGenerate}
        disabled={loading || prompt.trim() === ""}
      >
        {loading ? "Generating…" : "Generate report"}
      </button>
      {error && <p className="chat-error">{error}</p>}
      {report && !loading && <pre className="report-body">{report}</pre>}
      {!report && !loading && !error && (
        <p className="placeholder">Generate a report to see it here.</p>
      )}
    </Card>
  );
}
