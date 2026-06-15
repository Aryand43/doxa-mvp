import { useEffect, useState } from "react";
import { clearAuthToken, fetchCurrentUser, fetchSummary, hasStoredAuthToken } from "./api";
import type { AIResponse, AuthInfo } from "./types";
import { useTheme } from "./useTheme";
import { MetricStrip } from "../components/MetricStrip";
import { AssistantPanel } from "../features/assistant/AssistantPanel";
import { ReportsPanel } from "../features/reports/ReportsPanel";
import { CrawlerPanel } from "../features/crawler/CrawlerPanel";
import { ApiInspector } from "./ApiInspector";
import { LoginPage } from "./LoginPage";
import styles from "./App.module.css";

export default function App() {
  const [summary, setSummary] = useState<AIResponse | null>(null);
  const [user, setUser] = useState<AuthInfo | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    let active = true;
    fetchCurrentUser()
      .then((d) => active && setUser(d))
      .catch(() => {
        if (!active) return;
        if (hasStoredAuthToken()) {
          clearAuthToken();
        }
        setUser(null);
      })
      .finally(() => active && setAuthChecked(true));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!user) {
      setSummary(null);
      return;
    }
    let active = true;
    fetchSummary()
      .then((d) => active && setSummary(d))
      .catch(() => active && setSummary(null));
    return () => {
      active = false;
    };
  }, [user]);

  function logout() {
    clearAuthToken();
    setUser(null);
    setSummary(null);
  }

  if (!authChecked) {
    return (
      <div className={styles.boot}>
        <span className={styles.mark} aria-hidden />
        <p>Checking access...</p>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

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

        <div className={styles.sessionBar}>
          <div className={styles.sessionMeta}>
            <span>{user.user_id}</span>
            <span>{user.roles.join(", ") || "No role"}</span>
            <span>{user.companies[0] ?? "No tenant"}</span>
          </div>
          <button type="button" className="btn-secondary" onClick={logout}>
            Sign out
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

      <ApiInspector />
    </div>
  );
}
