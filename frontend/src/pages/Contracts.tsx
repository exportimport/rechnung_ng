import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { contractsApi } from "../api/contracts";
import DataTable, { type Column } from "../components/DataTable";
import { formatEuro, formatDate } from "../lib/format";
import type { Contract, ContractStatus } from "../types";

const STATUS_LABELS: Record<ContractStatus, string> = {
  active: "Aktiv",
  not_yet_active: "Noch nicht aktiv",
  cancelled: "Gekündigt",
};

const STATUS_COLORS: Record<ContractStatus, string> = {
  active: "bg-green-100 text-green-800",
  not_yet_active: "bg-yellow-100 text-yellow-800",
  cancelled: "bg-red-100 text-red-800",
};

const columns: Column<Contract & Record<string, unknown>>[] = [
  { key: "customer_name", label: "Kunde", sortable: true },
  { key: "plan_name", label: "Tarif", sortable: true },
  {
    key: "current_price",
    label: "Preis",
    render: (row) =>
      row.current_price != null ? formatEuro(row.current_price as number) : "—",
  },
  {
    key: "start_date",
    label: "Beginn",
    sortable: true,
    render: (row) => formatDate(row.start_date as string),
  },
  {
    key: "billing_cycle",
    label: "Zyklus",
    render: (row) => (row.billing_cycle === "monthly" ? "Monatlich" : "Quartalsweise"),
  },
  {
    key: "status",
    label: "Status",
    render: (row) => {
      const s = row.status as ContractStatus;
      return (
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[s]}`}>
          {STATUS_LABELS[s]}
        </span>
      );
    },
  },
];

export default function Contracts() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<ContractStatus | "">("");

  const { data: contracts = [], isLoading } = useQuery({
    queryKey: ["contracts", statusFilter],
    queryFn: () => contractsApi.list(statusFilter || undefined),
  });

  if (isLoading) return <p className="text-gray-500">Wird geladen…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Verträge</h1>
        <button
          onClick={() => navigate("/contracts/new")}
          className="px-4 py-2 bg-violet-500 text-white text-sm font-medium rounded-md hover:bg-violet-600"
        >
          Neuer Vertrag
        </button>
      </div>

      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ContractStatus | "")}
          className="rounded-md border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-violet-400 focus:outline-none"
        >
          <option value="">Alle Status</option>
          <option value="active">Aktiv</option>
          <option value="not_yet_active">Noch nicht aktiv</option>
          <option value="cancelled">Gekündigt</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        data={contracts as unknown as (Contract & Record<string, unknown>)[]}
        onRowClick={(row) => navigate(`/contracts/${row.id}`)}
        emptyMessage="Keine Verträge gefunden."
      />
    </div>
  );
}
