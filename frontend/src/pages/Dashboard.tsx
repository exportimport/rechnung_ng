import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../api/client";
import { invoicesApi } from "../api/invoices";
import { formatEuro, formatDate } from "../lib/format";

interface DashboardInvoice {
  id: number;
  invoice_number: string;
  customer_name: string;
  plan_name: string;
  amount: number;
  created_at: string;
  due_date: string;
  overdue: boolean;
  status: string;
}

interface DashboardData {
  draft_count: number;
  overdue_count: number;
  customer_count: number;
  last_month_revenue: number;
  last_quarter_revenue: number;
  draft_invoices: DashboardInvoice[];
}

// --- Card definitions ---

type CardId = "draft_count" | "overdue_count" | "customer_count" | "last_month_revenue" | "last_quarter_revenue";

interface CardDef {
  id: CardId;
  label: string;
  highlight: "blue" | "red" | "green" | "violet";
  format: (data: DashboardData) => string | number;
}

const CARD_DEFS: CardDef[] = [
  { id: "draft_count", label: "Offene Rechnungen", highlight: "blue", format: (d) => d.draft_count },
  {
    id: "overdue_count",
    label: "Überfällig",
    highlight: "red",
    format: (d) => d.overdue_count,
  },
  { id: "customer_count", label: "Kunden", highlight: "violet", format: (d) => d.customer_count },
  { id: "last_month_revenue", label: "Umsatz letzter Monat", highlight: "green", format: (d) => formatEuro(d.last_month_revenue) },
  { id: "last_quarter_revenue", label: "Umsatz letztes Quartal", highlight: "green", format: (d) => formatEuro(d.last_quarter_revenue) },
];

const DEFAULT_ORDER: CardId[] = CARD_DEFS.map((c) => c.id);
const LS_ORDER = "dashboard_card_order";
const LS_HIDDEN = "dashboard_card_hidden";

function loadOrder(): CardId[] {
  try {
    const raw = localStorage.getItem(LS_ORDER);
    if (raw) return JSON.parse(raw) as CardId[];
  } catch {}
  return DEFAULT_ORDER;
}

function loadHidden(): Set<CardId> {
  try {
    const raw = localStorage.getItem(LS_HIDDEN);
    if (raw) return new Set(JSON.parse(raw) as CardId[]);
  } catch {}
  return new Set();
}

// --- Highlight styles ---

const HIGHLIGHT_CLASSES: Record<string, string> = {
  blue: "bg-sky-100/60 text-sky-700",
  red: "bg-red-100/60 text-red-600",
  green: "bg-emerald-100/60 text-emerald-700",
  violet: "bg-violet-100/60 text-violet-700",
};

// --- Dashboard component ---

export default function Dashboard() {
  const queryClient = useQueryClient();

  const [order, setOrder] = useState<CardId[]>(loadOrder);
  const [hidden, setHidden] = useState<Set<CardId>>(loadHidden);
  const [editMode, setEditMode] = useState(false);

  const persist = useCallback((newOrder: CardId[], newHidden: Set<CardId>) => {
    localStorage.setItem(LS_ORDER, JSON.stringify(newOrder));
    localStorage.setItem(LS_HIDDEN, JSON.stringify([...newHidden]));
  }, []);

  const move = (id: CardId, dir: -1 | 1) => {
    const idx = order.indexOf(id);
    if (idx < 0) return;
    const next = [...order];
    const swap = idx + dir;
    if (swap < 0 || swap >= next.length) return;
    [next[idx], next[swap]] = [next[swap], next[idx]];
    setOrder(next);
    persist(next, hidden);
  };

  const hide = (id: CardId) => {
    const next = new Set(hidden);
    next.add(id);
    setHidden(next);
    persist(order, next);
  };

  const show = (id: CardId) => {
    const next = new Set(hidden);
    next.delete(id);
    setHidden(next);
    persist(order, next);
  };

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/dashboard"),
    refetchInterval: 60_000,
  });

  const sendMutation = useMutation({
    mutationFn: ({ id, template_id }: { id: number; template_id: string }) =>
      invoicesApi.send(id, template_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success("Rechnung versendet");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading) return <p className="text-violet-400">Wird geladen…</p>;
  if (!data) return null;

  const visibleCards = order.filter((id) => !hidden.has(id));
  const hiddenCards = order.filter((id) => hidden.has(id));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-violet-800">Dashboard</h1>
        <button
          onClick={() => setEditMode((v) => !v)}
          className={[
            "text-xs px-3 py-1.5 rounded-lg border transition-colors",
            editMode
              ? "bg-violet-600 text-white border-violet-600"
              : "text-violet-500 border-violet-200 hover:border-violet-400",
          ].join(" ")}
        >
          {editMode ? "Fertig" : "Anpassen"}
        </button>
      </div>

      {/* Stat cards */}
      <div className="flex flex-wrap gap-4 mb-8">
        {visibleCards.map((id, idx) => {
          const def = CARD_DEFS.find((c) => c.id === id)!;
          return (
            <div
              key={id}
              className={[
                "relative backdrop-blur-sm rounded-2xl border border-white/60 shadow-lg p-5 min-w-[140px]",
                HIGHLIGHT_CLASSES[def.highlight],
                editMode ? "ring-2 ring-violet-300" : "",
              ].join(" ")}
            >
              <p className="text-sm font-medium opacity-70 pr-4">{def.label}</p>
              <p className="text-3xl font-bold mt-1">{def.format(data)}</p>

              {editMode && (
                <div className="absolute top-2 right-2 flex gap-1">
                  <button
                    onClick={() => move(id, -1)}
                    disabled={idx === 0}
                    className="w-5 h-5 flex items-center justify-center rounded bg-white/70 text-gray-500 hover:text-gray-800 disabled:opacity-30 text-xs"
                    title="Nach links"
                  >
                    ‹
                  </button>
                  <button
                    onClick={() => move(id, 1)}
                    disabled={idx === visibleCards.length - 1}
                    className="w-5 h-5 flex items-center justify-center rounded bg-white/70 text-gray-500 hover:text-gray-800 disabled:opacity-30 text-xs"
                    title="Nach rechts"
                  >
                    ›
                  </button>
                  <button
                    onClick={() => hide(id)}
                    className="w-5 h-5 flex items-center justify-center rounded bg-white/70 text-red-400 hover:text-red-600 text-xs"
                    title="Ausblenden"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {/* Hidden cards shown as ghost tiles in edit mode */}
        {editMode &&
          hiddenCards.map((id) => {
            const def = CARD_DEFS.find((c) => c.id === id)!;
            return (
              <div
                key={id}
                className="relative backdrop-blur-sm rounded-2xl border border-dashed border-gray-300 bg-white/20 shadow p-5 min-w-[140px] opacity-50"
              >
                <p className="text-sm font-medium text-gray-400 pr-6">{def.label}</p>
                <p className="text-3xl font-bold mt-1 text-gray-300">—</p>
                <button
                  onClick={() => show(id)}
                  className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center rounded bg-white/70 text-green-500 hover:text-green-700 text-xs"
                  title="Einblenden"
                >
                  +
                </button>
              </div>
            );
          })}
      </div>

      {/* Invoice table */}
      <h2 className="text-lg font-semibold text-violet-700 mb-3">
        Versandbereit ({data.draft_count})
      </h2>

      {data.draft_invoices.length === 0 ? (
        <p className="text-violet-400">Keine offenen Rechnungen.</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/60 bg-white/70 backdrop-blur-sm shadow-lg">
          <table className="min-w-full divide-y divide-white/40 text-sm">
            <thead className="bg-white/40">
              <tr>
                {["Rechnungsnummer", "Kunde", "Plan", "Betrag", "Erstellt", "Fällig", ""].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-violet-700 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/40">
              {data.draft_invoices.map((inv) => (
                <tr key={inv.id} className={inv.overdue ? "bg-red-50/50" : ""}>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-gray-700">{inv.customer_name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{inv.plan_name}</td>
                  <td className="px-4 py-3 text-gray-700">{formatEuro(inv.amount)}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(inv.created_at)}</td>
                  <td className={["px-4 py-3", inv.overdue ? "text-red-600 font-medium" : "text-gray-500"].join(" ")}>
                    {formatDate(inv.due_date)}
                    {inv.overdue && " ⚠"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => sendMutation.mutate({ id: inv.id, template_id: "auto" })}
                      className="text-xs text-violet-600 hover:underline"
                    >
                      Senden
                    </button>
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
