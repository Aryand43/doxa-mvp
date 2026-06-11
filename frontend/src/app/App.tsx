import { useEffect, useState } from "react";
import { fetchSummary } from "./api";
import type { AIResponse } from "./types";
import { MetricStrip } from "../components/MetricStrip";
import { AssistantPanel } from "../features/assistant/AssistantPanel";
import { ReportsPanel } from "../features/reports/ReportsPanel";
import { CrawlerPanel } from "../features/crawler/CrawlerPanel";

export default function App() {
  const [summary, setSummary] = useState<AIResponse | null>(null);

  useEffect(() => {
    let active = true;
    fetchSummary()
      .then((d) => active && setSummary(d))
      .catch(() => active && setSummary(null));
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <h1>Doxa Connex AI</h1>
          <p className="app-subtitle">
            Procurement intelligence copilot — assistant, reports & data crawler,
            grounded in your operational data
          </p>
        </div>
        {summary ? (
          <MetricStrip metrics={summary.metrics} />
        ) : (
          <span className="app-snapshot-loading">Loading snapshot…</span>
        )}
      </header>

      <main className="app-panels">
        <AssistantPanel />
        <ReportsPanel />
        <CrawlerPanel />
      </main>
    </div>
  );
}
