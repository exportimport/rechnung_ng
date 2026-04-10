import { useState } from "react";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
}

interface Props<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

type SortDir = "asc" | "desc";

export default function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  onRowClick,
  emptyMessage = "Keine Einträge vorhanden.",
}: Props<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const sorted = sortKey
    ? [...data].sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        const cmp = String(av ?? "").localeCompare(String(bv ?? ""), "de");
        return sortDir === "asc" ? cmp : -cmp;
      })
    : data;

  return (
    <div className="overflow-x-auto rounded-2xl border border-white/60 bg-white/70 backdrop-blur-sm shadow-lg">
      <table className="min-w-full divide-y divide-white/40 text-sm">
        <thead className="bg-white/40">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={[
                  "px-4 py-3 text-left font-semibold text-violet-700 uppercase tracking-wider text-xs",
                  col.sortable ? "cursor-pointer select-none hover:text-violet-900" : "",
                ].join(" ")}
                onClick={col.sortable ? () => handleSort(col.key) : undefined}
              >
                {col.label}
                {col.sortable && sortKey === col.key && (
                  <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/40">
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-violet-400">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sorted.map((row, i) => (
              <tr
                key={i}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={onRowClick ? "cursor-pointer hover:bg-white/50 transition-colors" : ""}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-gray-700">
                    {col.render ? col.render(row) : String(row[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
