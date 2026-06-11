import styles from "./states.module.css";

export function LoadingState({ label = "Working" }: { label?: string }) {
  return (
    <div className={styles.loading} role="status">
      <div className={styles.bar} aria-hidden>
        <span />
      </div>
      <span className={styles.loadingLabel}>{label}</span>
    </div>
  );
}
