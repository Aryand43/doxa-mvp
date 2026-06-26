import type { TableData } from "../app/types";
import styles from "./DataTable.module.css";

function isNumericCell(cell: unknown): boolean {
  if (typeof cell === "number") return true;
  if (typeof cell !== "string") return false;
  const normalized = cell.replace(/,/g, "").trim();
  return normalized !== "" && /^-?\d+(\.\d+)?$/.test(normalized);
}

function isNumericColumn(rows: unknown[][], columnIndex: number): boolean {
  const cells = rows
    .map((row) => row[columnIndex])
    .filter((cell) => cell !== null && cell !== "" && cell !== undefined);
  if (!cells.length) return false;
  const numericCount = cells.filter(isNumericCell).length;
  return numericCount / cells.length >= 0.6;
}

export function DataTable({ table }: { table: TableData }) {
  if (!table.columns.length) return null;

  const numericColumns = table.columns.map((_, index) => isNumericColumn(table.rows, index));

  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <caption className={styles.caption}>
          {table.rows.length} {table.rows.length === 1 ? "row" : "rows"}
        </caption>
        <thead>
          <tr>
            {table.columns.map((column, index) => (
              <th
                key={index}
                className={numericColumns[index] ? styles.num : undefined}
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, columnIndex) => (
                <td
                  key={columnIndex}
                  className={numericColumns[columnIndex] ? styles.num : undefined}
                >
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
