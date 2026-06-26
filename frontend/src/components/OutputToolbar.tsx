import type { OutputMode } from "./AIResponseBody";
import styles from "./OutputToolbar.module.css";

type OutputToolbarProps = {
  mode: OutputMode;
  onModeChange: (mode: OutputMode) => void;
  hasTable: boolean;
  hasMetrics: boolean;
  onExport?: () => void;
  disabled?: boolean;
};

const MODES: { id: OutputMode; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "table", label: "Table" },
  { id: "chart", label: "Chart" },
];

export function OutputToolbar({
  mode,
  onModeChange,
  hasTable,
  hasMetrics,
  onExport,
  disabled,
}: OutputToolbarProps) {
  return (
    <div className={styles.toolbar} role="toolbar" aria-label="Output controls">
      <div className={styles.modes} role="group" aria-label="Output mode">
        {MODES.map((item) => {
          const unavailable =
            (item.id === "table" && !hasTable) || (item.id === "chart" && !hasMetrics);
          return (
            <button
              key={item.id}
              type="button"
              className={`${styles.mode} ${mode === item.id ? styles.modeOn : ""}`}
              aria-pressed={mode === item.id}
              disabled={disabled || unavailable}
              title={unavailable ? "Not available for this output" : undefined}
              onClick={() => onModeChange(item.id)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {onExport && (
        <button type="button" className="btn-secondary" onClick={onExport} disabled={disabled}>
          Export CSV
        </button>
      )}
    </div>
  );
}
