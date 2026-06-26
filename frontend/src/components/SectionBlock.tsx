import type { ReactNode } from "react";
import styles from "./SectionBlock.module.css";

/** Compact sectional divider for embedded enterprise modules. */
export function SectionBlock({
  eyebrow,
  title,
  meta,
  inset = false,
  children,
}: {
  eyebrow?: string;
  title: string;
  meta?: string;
  inset?: boolean;
  children: ReactNode;
}) {
  return (
    <section className={styles.block}>
      <header className={styles.header}>
        <div>
          {eyebrow && <span className={styles.eyebrow}>{eyebrow}</span>}
          <h3 className={styles.title}>{title}</h3>
        </div>
        {meta && <span className={styles.meta}>{meta}</span>}
      </header>
      <div className={inset ? styles.bodyInset : styles.body}>{children}</div>
    </section>
  );
}
