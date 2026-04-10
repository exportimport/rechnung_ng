import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { customersApi } from "../api/customers";
import DataTable, { type Column } from "../components/DataTable";
import type { Customer } from "../types";

const columns: Column<Customer & Record<string, unknown>>[] = [
  { key: "nachname", label: "Nachname", sortable: true },
  { key: "vorname", label: "Vorname", sortable: true },
  { key: "email", label: "E-Mail", sortable: true },
  {
    key: "iban",
    label: "IBAN",
    render: (row) => {
      const iban = row.iban as string;
      return iban.slice(0, 4) + " •••• " + iban.slice(-4);
    },
  },
];

export default function Customers() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ["customers", search],
    queryFn: () => customersApi.list(search || undefined),
  });

  const deleteMutation = useMutation({
    mutationFn: customersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Kunde gelöscht");
      setConfirmDelete(null);
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setConfirmDelete(null);
    },
  });

  if (isLoading) return <p className="text-gray-500">Wird geladen…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Kunden</h1>
        <button
          onClick={() => navigate("/customers/new")}
          className="px-4 py-2 bg-violet-500 text-white text-sm font-medium rounded-md hover:bg-violet-600"
        >
          Neuer Kunde
        </button>
      </div>

      <div className="mb-4">
        <input
          type="search"
          placeholder="Suche nach Name oder E-Mail…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-72 rounded-md border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-violet-400 focus:outline-none focus:ring-1 focus:ring-violet-400"
        />
      </div>

      <DataTable
        columns={columns}
        data={customers as unknown as (Customer & Record<string, unknown>)[]}
        onRowClick={(row) => navigate(`/customers/${row.id}`)}
        emptyMessage="Keine Kunden gefunden."
      />

      {confirmDelete !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full shadow-xl">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Kunde löschen?</h2>
            <p className="text-sm text-gray-500 mb-4">
              Diese Aktion kann nicht rückgängig gemacht werden.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 text-sm text-gray-700 border border-gray-200 rounded-md hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={() => deleteMutation.mutate(confirmDelete)}
                className="px-4 py-2 text-sm text-white bg-red-600 rounded-md hover:bg-red-700"
              >
                Löschen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
