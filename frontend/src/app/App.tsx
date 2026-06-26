import { useEffect, useMemo, useState } from "react";
import { clearAuthToken, fetchCurrentUser, fetchSummary, hasStoredAuthToken } from "./api";
import type { AIResponse, AuthInfo } from "./types";
import { useTheme } from "./useTheme";
import {
  accessibleFeatures,
  canAccessFeature,
  defaultFeature,
  FEATURES,
  type FeatureId,
} from "./features";
import { MetricStrip } from "../components/MetricStrip";
import { SessionBar } from "../components/SessionBar";
import { UnauthorizedPanel } from "../components/UnauthorizedPanel";
import { AssistantPanel } from "../features/assistant/AssistantPanel";
import { ReportsPanel } from "../features/reports/ReportsPanel";
import { CrawlerPanel } from "../features/crawler/CrawlerPanel";
import { ApiInspector } from "./ApiInspector";
import { LoginPage } from "./LoginPage";
import styles from "./App.module.css";

export default function App() {
  const [activeTab, setActiveTab] = useState<FeatureId>("assistant");
  const [summary, setSummary] = useState<AIResponse | null>(null);
  const [user, setUser] = useState<AuthInfo | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const allowedFeatures = useMemo(
    () => (user ? accessibleFeatures(user) : []),
    [user],
  );

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
    setActiveTab((current) =>
      canAccessFeature(user, current) ? current : defaultFeature(user),
    );
  }, [user]);

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

  const activeFeature = FEATURES.find((feature) => feature.id === activeTab);

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

        <SessionBar user={user} onLogout={logout} />

        <div className={styles.snapshot}>
          <span className={styles.snapshotKicker}>Live snapshot</span>
          {summary ? (
            <MetricStrip metrics={summary.metrics} variant="tape" />
          ) : (
            <span className={styles.snapshotLoading}>Live snapshot unavailable for this session</span>
          )}
        </div>
      </header>

      <nav className={styles.tabBar} aria-label="Product features">
        {FEATURES.map((feature) => {
          const allowed = allowedFeatures.some((item) => item.id === feature.id);
          const selected = activeTab === feature.id;
          return (
            <button
              key={feature.id}
              type="button"
              role="tab"
              id={`tab-${feature.id}`}
              aria-selected={selected}
              aria-controls={`panel-${feature.id}`}
              className={
                selected ? styles.tabActive : allowed ? styles.tab : styles.tabDenied
              }
              disabled={!allowed}
              onClick={() => allowed && setActiveTab(feature.id)}
              title={allowed ? feature.hint : `Requires ${feature.authority}`}
            >
              <span className={styles.tabLabel}>{feature.label}</span>
              <span className={styles.tabHint}>
                {allowed ? feature.hint : `Requires ${feature.authority}`}
              </span>
            </button>
          );
        })}
      </nav>

      <main className={styles.tabContent}>
        {FEATURES.map((feature) => {
          if (activeTab !== feature.id) return null;
          const allowed = canAccessFeature(user, feature.id);
          return (
            <div
              key={feature.id}
              role="tabpanel"
              id={`panel-${feature.id}`}
              aria-labelledby={`tab-${feature.id}`}
              className={styles.tabPanel}
            >
              {!allowed ? (
                <UnauthorizedPanel
                  featureLabel={feature.label}
                  requiredAuthority={feature.authority}
                />
              ) : feature.id === "assistant" ? (
                <AssistantPanel />
              ) : feature.id === "reports" ? (
                <ReportsPanel />
              ) : (
                <CrawlerPanel />
              )}
            </div>
          );
        })}
      </main>

      {allowedFeatures.length === 0 && activeFeature && (
        <p className={styles.noAccessBanner}>
          No AI modules are enabled for this session. Sign in with a profile that includes at least
          one module authority.
        </p>
      )}

      <ApiInspector />
    </div>
  );
}
