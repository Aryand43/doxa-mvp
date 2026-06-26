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

type FeatureTab = "assistant" | "reports" | "crawler";

const FEATURE_TABS: { id: FeatureTab; label: string; hint: string }[] = [
  { id: "assistant", label: "Assistant", hint: "Ask questions grounded in procurement data" },
  { id: "reports", label: "Reports", hint: "Structured spend, vendor, and entity reports" },
  { id: "crawler", label: "Crawler", hint: "Scan datasets for alerts and anomalies" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<FeatureTab>("assistant");
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

      <nav className={styles.tabBar} aria-label="Product features">
        {FEATURE_TABS.map((tab) => {
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`tab-${tab.id}`}
              aria-selected={selected}
              aria-controls={`panel-${tab.id}`}
              className={selected ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className={styles.tabLabel}>{tab.label}</span>
              <span className={styles.tabHint}>{tab.hint}</span>
            </button>
          );
        })}
      </nav>

      <main className={styles.tabContent}>
        <div
          role="tabpanel"
          id="panel-assistant"
          aria-labelledby="tab-assistant"
          hidden={activeTab !== "assistant"}
          className={styles.tabPanel}
        >
          <AssistantPanel />
        </div>
        <div
          role="tabpanel"
          id="panel-reports"
          aria-labelledby="tab-reports"
          hidden={activeTab !== "reports"}
          className={styles.tabPanel}
        >
          <ReportsPanel />
        </div>
        <div
          role="tabpanel"
          id="panel-crawler"
          aria-labelledby="tab-crawler"
          hidden={activeTab !== "crawler"}
          className={styles.tabPanel}
        >
          <CrawlerPanel />
        </div>
      </main>

      <ApiInspector />
    </div>
  );
}
