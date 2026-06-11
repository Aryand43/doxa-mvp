import type { ScanPhase } from "../app/types";
import styles from "./ScanProcessing.module.css";

const FALLBACK_STEPS: ScanPhase[] = [
  { id: "load", label: "Loading procurement datasets", detail: "" },
  { id: "duplicate", label: "Running duplicate invoice detector", detail: "" },
  { id: "anomalous_spend", label: "Running anomalous spend detector", detail: "" },
  { id: "price_variance", label: "Running price variance detector", detail: "" },
  { id: "vendor_risk", label: "Running vendor risk detector", detail: "" },
  { id: "contract_expiry", label: "Running contract expiry detector", detail: "" },
  { id: "compose", label: "Composing scan digest", detail: "" },
];

export function ScanProcessing({
  phases,
  activeIndex,
  complete = false,
}: {
  phases?: ScanPhase[];
  activeIndex: number;
  complete?: boolean;
}) {
  const steps = phases && phases.length > 0 ? phases : FALLBACK_STEPS;

  return (
    <ol className={styles.list} aria-label="Scan processing steps">
      {steps.map((step, i) => {
        const done = complete || i < activeIndex;
        const active = !complete && i === activeIndex;
        return (
          <li
            key={step.id}
            className={`${styles.item} ${done ? styles.done : ""} ${active ? styles.active : ""}`}
          >
            <span className={styles.marker} aria-hidden>
              {done ? "✓" : active ? "…" : "·"}
            </span>
            <div className={styles.body}>
              <span className={styles.label}>{step.label}</span>
              {(step.detail || (active && !complete)) && (
                <span className={styles.detail}>
                  {step.detail || (active ? "Processing…" : "")}
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
