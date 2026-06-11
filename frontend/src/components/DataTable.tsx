import type { TableData } from "../app/types";

export function DataTable({ table }: { table: TableData }) {
  if (!table.columns.length) return null;
  return (
    <div className="data-table-wrap">
      <table className="data-table">
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
                <td key={ci}>{cell === null || cell === "" ? "—" : String(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
