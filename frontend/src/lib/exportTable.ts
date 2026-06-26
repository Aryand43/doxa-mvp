import type { TableData } from "../app/types";

function escapeCsvCell(value: string | number | null): string {
  const text = value === null ? "" : String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function tableToCsv(table: TableData): string {
  const header = table.columns.map(escapeCsvCell).join(",");
  const rows = table.rows.map((row) => row.map(escapeCsvCell).join(","));
  return [header, ...rows].join("\n");
}

export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
