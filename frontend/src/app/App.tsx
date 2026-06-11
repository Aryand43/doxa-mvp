import { useEffect, useState } from "react";
import { fetchSummary } from "./api";
import type { AIResponse } from "./types";
import { useTheme } from "./useTheme";
import { MetricStrip } from "../components/MetricStrip";
import { AssistantPanel } from "../features/assistant/AssistantPanel";
import { ReportsPanel } from "../features/reports/ReportsPanel";
import { CrawlerPanel } from "../features/crawler/CrawlerPanel";
import styles from "./App.module.css";

export default function App() {
  const [summary, setSummary] = useState<AIResponse | null>(null);
  const { theme, toggleTheme } = useTheme();

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
    <div className={styles.app}>
      <header className={styles.masthead}>
        <div className={styles.mastheadTop}>
          <div className={styles.brand}>
            <span className={styles.mark} aria-hidden />
            <div>
              <p className={styles.wordmark}>
                Doxa Connex <span className={styles.tag}>AI</span>
              </p>
              <p className={styles.subtitle}>
                Procurement intelligence, grounded in your operational data.
              </p>
            </div>
          </div>
          <button
            type="button"
            className={styles.themeToggle}
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            aria-pressed={theme === "dark"}
          >
            <span className={styles.themeIcon} aria-hidden>
              {theme === "dark" ? "☀" : "☾"}
            </span>
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </div>

        <div className={styles.snapshot}>
          <span className={styles.snapshotKicker}>Live snapshot</span>
          {summary ? (
            <MetricStrip metrics={summary.metrics} variant="tape" />
          ) : (
            <span className={styles.snapshotLoading}>Loading live snapshot…</span>
          )}
        </div>
      </header>

      <main className={styles.stations}>
        <AssistantPanel />
        <ReportsPanel />
        <CrawlerPanel />
      </main>
    </div>
  );
}
