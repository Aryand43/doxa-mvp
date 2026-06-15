import { useCallback, useEffect, useState } from "react";
import { checkBackendHealth, scalarUrl } from "./api";
import {
  clearApiCalls,
  getApiCalls,
  getBackendHealth,
  isApiDebugEnabled,
  subscribeApiDebug,
  type ApiCallRecord,
  type BackendHealth,
} from "./apiDebug";
import styles from "./ApiInspector.module.css";

const HEALTH_LABEL: Record<BackendHealth, string> = {
  healthy: "Healthy",
  unhealthy: "Unhealthy",
  unknown: "Unknown",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function CallRow({ call }: { call: ApiCallRecord }) {
  const [open, setOpen] = useState(false);

  return (
    <li className={styles.call}>
      <button
        type="button"
        className={styles.callHead}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className={call.ok ? styles.ok : styles.fail} aria-hidden>
          {call.ok ? "✓" : "✕"}
        </span>
        <span className={styles.method}>{call.method}</span>
        <span className={styles.path}>{call.url}</span>
        <span className={styles.meta}>
          {call.status ?? "—"} · {call.durationMs}ms
        </span>
        <span className={styles.time}>{formatTime(call.timestamp)}</span>
      </button>
      {open && (
        <div className={styles.callBody}>
          {call.requestBody !== undefined && (
            <pre>{JSON.stringify(call.requestBody, null, 2)}</pre>
          )}
          {call.responseBody !== undefined && (
            <pre>{JSON.stringify(call.responseBody, null, 2)}</pre>
          )}
          {call.error && <p className={styles.error}>{call.error}</p>}
        </div>
      )}
    </li>
  );
}

export function ApiInspector() {
  const [open, setOpen] = useState(false);
  const [, tick] = useState(0);
  const refresh = useCallback(() => tick((n) => n + 1), []);

  useEffect(() => {
    if (!isApiDebugEnabled()) return;
    return subscribeApiDebug(refresh);
  }, [refresh]);

  useEffect(() => {
    if (!isApiDebugEnabled()) return;

    void checkBackendHealth();
    const id = window.setInterval(() => void checkBackendHealth(), 30_000);
    return () => window.clearInterval(id);
  }, []);

  if (!isApiDebugEnabled()) return null;

  const health = getBackendHealth();
  const calls = getApiCalls();

  return (
    <div className={styles.root} aria-live="polite">
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="api-inspector-panel"
      >
        <span className={`${styles.healthDot} ${styles[`health_${health}`]}`} aria-hidden />
        API {calls.length > 0 ? `(${calls.length})` : ""}
      </button>

      {open && (
        <section id="api-inspector-panel" className={styles.panel}>
          <header className={styles.panelHead}>
            <div>
              <p className={styles.title}>API Inspector</p>
              <p className={styles.subtitle}>Browser transport log</p>
            </div>
            <div className={styles.headActions}>
              <span className={`${styles.badge} ${styles[`health_${health}`]}`}>
                /health · {HEALTH_LABEL[health]}
              </span>
              <button type="button" className={styles.clearBtn} onClick={clearApiCalls}>
                Clear
              </button>
            </div>
          </header>

          <p className={styles.hint}>
            <a href={scalarUrl()} target="_blank" rel="noreferrer">
              /scalar
            </a>{" "}
            = API contract · this panel = live requests
          </p>

          {calls.length === 0 ? (
            <p className={styles.empty}>No API calls yet.</p>
          ) : (
            <ul className={styles.list}>
              {calls.map((call) => (
                <CallRow key={call.id} call={call} />
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
