import type { ReactNode } from "react";
import styles from "./Panel.module.css";

/**
 * Shared "station" shell for the three surfaces (Assistant, Reports, Crawler).
 * Genuinely shared layout: a mono verb kicker, title, description, an optional
 * controls strip, a scrollable body, and an optional pinned footer.
 */
export function Panel({
  kicker,
  title,
  description,
  controls,
  footer,
  children,
}: {
  kicker: string;
  title: string;
  description?: string;
  controls?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className={styles.panel}>
      <header className={styles.header}>
        <span className={styles.kicker}>{kicker}</span>
        <h2 className={styles.title}>{title}</h2>
        {description && <p className={styles.desc}>{description}</p>}
      </header>
      {controls && <div className={styles.controls}>{controls}</div>}
      <div className={styles.body}>{children}</div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </section>
  );
}
