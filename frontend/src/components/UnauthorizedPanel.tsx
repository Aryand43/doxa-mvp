import styles from "./UnauthorizedPanel.module.css";

export function UnauthorizedPanel({
  featureLabel,
  requiredAuthority,
}: {
  featureLabel: string;
  requiredAuthority: string;
}) {
  return (
    <section className={styles.panel} aria-labelledby="unauthorized-title">
      <p className={styles.kicker}>Access restricted</p>
      <h2 id="unauthorized-title" className={styles.title}>
        {featureLabel} unavailable
      </h2>
      <p className={styles.message}>
        Your current session does not include the <code>{requiredAuthority}</code> authority
        required for this module. Switch to an authorized profile or contact your administrator.
      </p>
      <p className={styles.note}>
        Authorization is enforced by the backend — the UI hides modules you cannot use, but API
        calls will still return 403 if access is missing.
      </p>
    </section>
  );
}
