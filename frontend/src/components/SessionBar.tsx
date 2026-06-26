import { formatTenantLabel } from "../app/auth";
import type { AuthInfo } from "../app/types";
import styles from "./SessionBar.module.css";

export function SessionBar({ user, onLogout }: { user: AuthInfo; onLogout: () => void }) {
  return (
    <div className={styles.bar}>
      <dl className={styles.meta}>
        <div className={styles.item}>
          <dt>User</dt>
          <dd>{user.user_id}</dd>
        </div>
        <div className={styles.item}>
          <dt>Roles</dt>
          <dd>{user.roles.join(", ") || "None"}</dd>
        </div>
        <div className={styles.item}>
          <dt>Tenant</dt>
          <dd title={user.companies.join(", ")}>{formatTenantLabel(user.companies)}</dd>
        </div>
        <div className={styles.itemWide}>
          <dt>Access</dt>
          <dd className={styles.authorities}>
            {user.authorities.length > 0 ? (
              user.authorities.map((authority) => (
                <span key={authority} className={styles.chip}>
                  {authority}
                </span>
              ))
            ) : (
              <span className={styles.chipMuted}>No module access</span>
            )}
          </dd>
        </div>
      </dl>
      <button type="button" className="btn-secondary" onClick={onLogout}>
        Sign out
      </button>
    </div>
  );
}
