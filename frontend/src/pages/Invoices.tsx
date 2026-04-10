import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { invoicesApi } from "../api/invoices";
import DataTable, { type Column } from "../components/DataTable";
import { formatEuro, formatDate } from "../lib/format";
import type { Invoice } from "../types";

const MONTHS = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

const currentYear = new Date().getFullYear();
const YEARS = [currentYear - 1, currentYear, currentYear + 1];

export default function Invoices() {
  const queryClient = useQueryClient();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ["invoices", year, month],
    queryFn: () => invoicesApi.list({ year, month }),
  });

  const generateMutation = useMutation({
    mutationFn: () => invoicesApi.generate(year, month),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success(`${data.length} Rechnung(en) erstellt`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const sendMutation = useMutation({
    mutationFn: ({ id, template_id }: { id: number; template_id: string }) =>
      invoicesApi.send(id, template_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success("Rechnung versendet");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const batchSendMutation = useMutation({
    mutationFn: () => invoicesApi.sendBatch(year, month),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success(`${data.length} Rechnung(en) versendet`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const draftCount = invoices.filter((i) => i.status === "draft").length;

  const columns: Column<Invoice & Record<string, unknown>>[] = [
    { key: "invoice_number", label: "Rechnungsnummer", sortable: true },
    {
      key: "amount",
      label: "Betrag",
      render: (row) => formatEuro(row.amount as number),
    },
    {
      key: "period_start",
      label: "Zeitraum",
      render: (row) =>
        `${formatDate(row.period_start as string)} – ${formatDate(row.period_end as string)}`,
    },
    {
      key: "status",
      label: "Status",
      render: (row) => (
        <span
          className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
            row.status === "draft"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-green-100 text-green-800"
          }`}
        >
          {row.status === "draft" ? "Entwurf" : "Versendet"}
        </span>
      ),
    },
    {
      key: "actions",
      label: "",
      render: (row) => (
        <div className="flex gap-2">
          <a
            href={invoicesApi.pdfUrl(row.id as number)}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-indigo-600 hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            PDF
          </a>
          {row.status === "draft" && (
            <button
              className="text-xs text-green-700 hover:underline"
              onClick={(e) => {
                e.stopPropagation();
                sendMutation.mutate({ id: row.id as number, template_id: "auto" });
              }}
            >
              Senden
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Rechnungen</h1>
        <div className="flex gap-2">
          {draftCount > 0 && (
            <button
              onClick={() => batchSendMutation.mutate()}
              className="px-4 py-2 text-sm font-medium text-green-700 border border-green-300 rounded-md hover:bg-green-50"
            >
              Alle {draftCount} Entwürfe senden
            </button>
          )}
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            Rechnungen generieren
          </button>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {MONTHS.map((m, i) => (
            <option key={i + 1} value={i + 1}>{m}</option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {YEARS.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-gray-500">Wird geladen…</p>
      ) : (
        <DataTable
          columns={columns}
          data={invoices as unknown as (Invoice & Record<string, unknown>)[]}
          emptyMessage="Keine Rechnungen für diesen Monat."
        />
      )}
    </div>
  );
}
