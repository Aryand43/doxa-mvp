import { useEffect, useState, type FormEvent } from "react";
import { fetchLoginOptions, loginWithProfile } from "./api";
import type { AuthInfo, DevAccessProfile, DevTenant } from "./types";
import styles from "./LoginPage.module.css";

export function LoginPage({ onLogin }: { onLogin: (user: AuthInfo) => void }) {
  const [tenants, setTenants] = useState<DevTenant[]>([]);
  const [profiles, setProfiles] = useState<DevAccessProfile[]>([]);
  const [userId, setUserId] = useState("demo-executive");
  const [buyerCompanyUuid, setBuyerCompanyUuid] = useState("");
  const [profileId, setProfileId] = useState("executive");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchLoginOptions()
      .then((options) => {
        if (!active) return;
        setTenants(options.tenants);
        setProfiles(options.profiles);
        setBuyerCompanyUuid(options.tenants[0]?.buyer_company_uuid ?? "");
        setProfileId(options.profiles[0]?.id ?? "executive");
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Login options could not be loaded.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!buyerCompanyUuid || !profileId || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await loginWithProfile({
        userId,
        buyerCompanyUuid,
        profileId,
      });
      onLogin(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <main className={styles.shell}>
        <section className={styles.brandPanel}>
          <span className={styles.mark} aria-hidden />
          <p className={styles.wordmark}>
            Doxa Connex <span>AI</span>
          </p>
          <h1>Secure procurement workspace</h1>
          <p className={styles.copy}>
            Sign in with a scoped tenant profile to test assistant, reports, crawler, RBAC,
            and row-level data isolation.
          </p>
          <dl className={styles.checks}>
            <div>
              <dt>Token</dt>
              <dd>JWT stored in browser storage</dd>
            </div>
            <div>
              <dt>Scope</dt>
              <dd>Data filtered by buyer company UUID</dd>
            </div>
            <div>
              <dt>Access</dt>
              <dd>Authorities checked per AI module</dd>
            </div>
          </dl>
        </section>

        <form className={styles.form} onSubmit={onSubmit}>
          <header>
            <span className={styles.kicker}>Access</span>
            <h2>Login</h2>
          </header>

          <label className={styles.field}>
            <span>User ID</span>
            <input
              type="text"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              autoComplete="username"
              disabled={loading || submitting}
            />
          </label>

          <label className={styles.field}>
            <span>Tenant</span>
            <select
              value={buyerCompanyUuid}
              onChange={(event) => setBuyerCompanyUuid(event.target.value)}
              disabled={loading || submitting || tenants.length === 0}
            >
              {tenants.map((tenant) => (
                <option key={tenant.buyer_company_uuid} value={tenant.buyer_company_uuid}>
                  {tenant.entity_name}
                </option>
              ))}
            </select>
          </label>

          <label className={styles.field}>
            <span>Access Profile</span>
            <select
              value={profileId}
              onChange={(event) => setProfileId(event.target.value)}
              disabled={loading || submitting || profiles.length === 0}
            >
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.label}
                </option>
              ))}
            </select>
          </label>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" disabled={loading || submitting || !buyerCompanyUuid || !profileId}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </main>
    </div>
  );
}
