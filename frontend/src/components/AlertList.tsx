import type { AlertItem } from "../app/types";
import type { ReviewDisposition } from "./AlertReviewActions";
import { AlertReviewActions } from "./AlertReviewActions";
import styles from "./AlertList.module.css";

function severityKey(severity: string): "high" | "medium" | "low" {
  const s = severity.toLowerCase();
  if (s === "high") return "high";
  if (s === "medium") return "medium";
  return "low";
}

const SEV_ITEM = { high: styles.sevHigh, medium: styles.sevMedium, low: styles.sevLow };
const SEV_BADGE = {
  high: styles.badgeHigh,
  medium: styles.badgeMedium,
  low: styles.badgeLow,
};

type AlertListProps = {
  alerts: AlertItem[];
  reviewable?: boolean;
  dispositions?: Record<string, ReviewDisposition | undefined>;
  onReview?: (alertId: string, disposition: ReviewDisposition) => void;
};

export function AlertList({
  alerts,
  reviewable = false,
  dispositions,
  onReview,
}: AlertListProps) {
  if (alerts.length === 0) return null;
  return (
    <ul className={styles.list}>
      {alerts.map((a) => {
        const sev = severityKey(a.severity);
        const disposition = dispositions?.[a.id];
        return (
          <li
            key={a.id}
            className={`${styles.item} ${SEV_ITEM[sev]} ${disposition ? styles.reviewed : ""}`}
          >
            <div className={styles.head}>
              <span className={`${styles.badge} ${SEV_BADGE[sev]}`}>{sev}</span>
              <span className={styles.type}>{a.type.replace(/_/g, " ")}</span>
              <span className={styles.source}>{a.source}</span>
            </div>
            <p className={styles.title}>{a.title}</p>
            {a.description && <p className={styles.desc}>{a.description}</p>}
            {a.records.length > 0 && (
              <p className={styles.records}>{a.records.slice(0, 6).join("  ·  ")}</p>
            )}
            {a.recommended_action && (
              <p className={styles.action}>
                <span className={styles.actionLabel}>Recommended</span>
                {a.recommended_action}
              </p>
            )}
            {reviewable && onReview && (
              <AlertReviewActions
                disposition={disposition}
                onSelect={(next) => onReview(a.id, next)}
              />
            )}
          </li>
        );
      })}
    </ul>
  );
}
