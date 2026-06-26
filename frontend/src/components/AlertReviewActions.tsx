import styles from "./AlertReviewActions.module.css";

export type ReviewDisposition = "ignore" | "confirm" | "escalate" | "learn";

const ACTIONS: { id: ReviewDisposition; label: string }[] = [
  { id: "ignore", label: "Ignore" },
  { id: "confirm", label: "Confirm" },
  { id: "escalate", label: "Escalate" },
  { id: "learn", label: "Learn" },
];

export function AlertReviewActions({
  disposition,
  onSelect,
}: {
  disposition?: ReviewDisposition;
  onSelect: (disposition: ReviewDisposition) => void;
}) {
  return (
    <div className={styles.wrap} role="group" aria-label="Review alert">
      {ACTIONS.map((action) => (
        <button
          key={action.id}
          type="button"
          className={`${styles.action} ${disposition === action.id ? styles.actionOn : ""}`}
          aria-pressed={disposition === action.id}
          onClick={() => onSelect(action.id)}
        >
          {action.label}
        </button>
      ))}
      {disposition && (
        <span className={styles.status} aria-live="polite">
          Marked {disposition}
        </span>
      )}
    </div>
  );
}
