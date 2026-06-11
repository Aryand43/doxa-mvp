import type { TableData } from "../app/types";
import styles from "./DataTable.module.css";

export function DataTable({ table }: { table: TableData }) {
  if (!table.columns.length) return null;
  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {table.columns.map((c, i) => (
              <th key={i}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci} className={typeof cell === "number" ? styles.num : undefined}>
                  {cell === null || cell === "" ? "—" : String(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
