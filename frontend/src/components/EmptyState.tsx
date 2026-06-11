import styles from "./states.module.css";

export function EmptyState({ title, message }: { title?: string; message: string }) {
  return (
    <div className={styles.empty}>
      {title && <p className={styles.emptyTitle}>{title}</p>}
      <p className={styles.emptyMsg}>{message}</p>
    </div>
  );
}
