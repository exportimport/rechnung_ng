import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { invoicesApi } from "../api/invoices";
import { formatEuro, formatDate } from "../lib/format";
import type { Invoice, InvoiceStatus } from "../types";

const MONTHS = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

const currentYear = new Date().getFullYear();
const YEARS = [currentYear - 1, currentYear, currentYear + 1];

type StatusFilter = "all" | InvoiceStatus;

export default function Invoices() {
  const queryClient = useQueryClient();
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selected, setSelected] = useState<Set<number>>(new Set());

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

  const deleteMutation = useMutation({
    mutationFn: (id: number) => invoicesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Entwurf gelöscht");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => invoicesApi.bulkDelete(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSelected(new Set());
      toast.success("Entwürfe gelöscht");
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

  const drafts = invoices.filter((i) => i.status === "draft");
  const filtered = statusFilter === "all" ? invoices : invoices.filter((i) => i.status === statusFilter);
  const visibleDraftIds = filtered.filter((i) => i.status === "draft").map((i) => i.id);
  const allVisibleDraftsSelected =
    visibleDraftIds.length > 0 && visibleDraftIds.every((id) => selected.has(id));

  function toggleRow(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleSelectAllDrafts() {
    if (allVisibleDraftsSelected) {
      setSelected((prev) => {
        const next = new Set(prev);
        visibleDraftIds.forEach((id) => next.delete(id));
        return next;
      });
    } else {
      setSelected((prev) => new Set([...prev, ...visibleDraftIds]));
    }
  }

  function handleBulkDelete() {
    const ids = [...selected];
    if (ids.length === 0) return;
    if (!confirm(`${ids.length} Entwurf/Entwürfe wirklich löschen?`)) return;
    bulkDeleteMutation.mutate(ids);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-violet-800">Rechnungen</h1>
        <div className="flex gap-2">
          {drafts.length > 0 && (
            <button
              onClick={() => batchSendMutation.mutate()}
              className="px-5 py-2 text-sm font-medium text-violet-700 border border-violet-300 rounded-full hover:bg-white/60 backdrop-blur-sm transition-colors"
            >
              Alle {drafts.length} Entwürfe senden
            </button>
          )}
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="px-5 py-2 bg-violet-500 text-white text-sm font-medium rounded-full hover:bg-violet-600 shadow-sm disabled:opacity-50 transition-colors"
          >
            Rechnungen generieren
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={month}
          onChange={(e) => { setMonth(Number(e.target.value)); setSelected(new Set()); }}
          className="rounded-full border border-white/60 bg-white/70 backdrop-blur-sm px-4 py-2 text-sm"
        >
          {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
        </select>
        <select
          value={year}
          onChange={(e) => { setYear(Number(e.target.value)); setSelected(new Set()); }}
          className="rounded-full border border-white/60 bg-white/70 backdrop-blur-sm px-4 py-2 text-sm"
        >
          {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        <div className="flex rounded-full border border-white/60 bg-white/70 backdrop-blur-sm overflow-hidden text-sm">
          {(["all", "draft", "sent"] as StatusFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setSelected(new Set()); }}
              className={`px-4 py-2 transition-colors ${statusFilter === s ? "bg-violet-500 text-white" : "hover:bg-white/60"}`}
            >
              {s === "all" ? "Alle" : s === "draft" ? "Entwurf" : "Versendet"}
            </button>
          ))}
        </div>
      </div>

      {/* Bulk action bar */}
      {visibleDraftIds.length > 0 && (
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={toggleSelectAllDrafts}
            className="text-sm text-violet-600 hover:underline"
          >
            {allVisibleDraftsSelected ? "Auswahl aufheben" : `Alle ${visibleDraftIds.length} Entwürfe auswählen`}
          </button>
          {selected.size > 0 && (
            <button
              onClick={handleBulkDelete}
              disabled={bulkDeleteMutation.isPending}
              className="px-4 py-1.5 text-sm font-medium bg-red-500 text-white rounded-full hover:bg-red-600 disabled:opacity-50 transition-colors"
            >
              {selected.size} löschen
            </button>
          )}
        </div>
      )}

      {isLoading ? (
        <p className="text-violet-400">Wird geladen…</p>
      ) : filtered.length === 0 ? (
        <p className="text-violet-400">Keine Rechnungen für diesen Monat.</p>
      ) : (
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl border border-white/60 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-violet-100 text-left text-violet-500 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3">Rechnungsnummer</th>
                <th className="px-4 py-3">Betrag</th>
                <th className="px-4 py-3">Zeitraum</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row: Invoice) => (
                <tr
                  key={row.id}
                  className={`border-b border-violet-50 last:border-0 transition-colors ${selected.has(row.id) ? "bg-violet-50" : "hover:bg-white/40"}`}
                >
                  <td className="px-4 py-3">
                    {row.status === "draft" && (
                      <input
                        type="checkbox"
                        checked={selected.has(row.id)}
                        onChange={() => toggleRow(row.id)}
                        className="accent-violet-500 w-4 h-4"
                      />
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{row.invoice_number}</td>
                  <td className="px-4 py-3">{formatEuro(row.amount)}</td>
                  <td className="px-4 py-3 text-violet-500">
                    {formatDate(row.period_start)} – {formatDate(row.period_end)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-3 py-0.5 rounded-full text-xs font-medium ${row.status === "draft" ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700"}`}>
                      {row.status === "draft" ? "Entwurf" : "Versendet"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3 justify-end">
                      <a
                        href={invoicesApi.pdfUrl(row.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-violet-600 hover:underline"
                      >
                        PDF
                      </a>
                      {row.status === "draft" && (
                        <>
                          <button
                            className="text-xs text-green-700 hover:underline"
                            onClick={() => sendMutation.mutate({ id: row.id, template_id: "auto" })}
                          >
                            Senden
                          </button>
                          <button
                            className="text-xs text-red-500 hover:underline"
                            onClick={() => deleteMutation.mutate(row.id)}
                          >
                            Löschen
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
