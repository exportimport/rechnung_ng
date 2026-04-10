import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { plansApi } from "../api/plans";
import DataTable, { type Column } from "../components/DataTable";
import { formatEuro, formatDate } from "../lib/format";
import type { Plan } from "../types";

const columns: Column<Plan & Record<string, unknown>>[] = [
  { key: "name", label: "Tarifname", sortable: true },
  {
    key: "current_price",
    label: "Aktueller Preis",
    render: (row) =>
      row.current_price != null ? formatEuro(row.current_price as number) : "—",
  },
  {
    key: "price_history",
    label: "Gültig seit",
    render: (row) => {
      const history = row.price_history as Plan["price_history"];
      if (!history.length) return "—";
      const last = history[history.length - 1];
      return formatDate(last.valid_from);
    },
  },
];

export default function Plans() {
  const navigate = useNavigate();
  const { data: plans = [], isLoading } = useQuery({
    queryKey: ["plans"],
    queryFn: plansApi.list,
  });

  if (isLoading) return <p className="text-gray-500">Wird geladen…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Tarife</h1>
        <button
          onClick={() => navigate("/plans/new")}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
        >
          Neuer Tarif
        </button>
      </div>

      <DataTable
        columns={columns}
        data={plans as unknown as (Plan & Record<string, unknown>)[]}
        onRowClick={(row) => navigate(`/plans/${row.id}`)}
        emptyMessage="Keine Tarife vorhanden."
      />

      {plans.length > 0 && (
        <div className="mt-2 text-xs text-gray-400">Zeile anklicken zum Bearbeiten</div>
      )}
    </div>
  );
}
