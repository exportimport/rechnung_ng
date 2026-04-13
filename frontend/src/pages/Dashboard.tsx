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

interface StatCardProps {
  label: string;
  value: string | number;
  highlight?: "blue" | "red" | "green" | "violet";
}

function StatCard({ label, value, highlight = "blue" }: StatCardProps) {
  const colors: Record<string, string> = {
    blue: "bg-sky-100/60 text-sky-700",
    red: "bg-red-100/60 text-red-600",
    green: "bg-emerald-100/60 text-emerald-700",
    violet: "bg-violet-100/60 text-violet-700",
  };
  return (
    <div className={`${colors[highlight]} backdrop-blur-sm rounded-2xl border border-white/60 shadow-lg p-5`}>
      <p className="text-sm font-medium opacity-70">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();

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

  return (
    <div>
      <h1 className="text-2xl font-bold text-violet-800 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        <StatCard label="Offene Rechnungen" value={data.draft_count} highlight="blue" />
        <StatCard
          label="Überfällig"
          value={data.overdue_count}
          highlight={data.overdue_count > 0 ? "red" : "blue"}
        />
        <StatCard label="Kunden" value={data.customer_count} highlight="violet" />
        <StatCard label="Umsatz letzter Monat" value={formatEuro(data.last_month_revenue)} highlight="green" />
        <StatCard label="Umsatz letztes Quartal" value={formatEuro(data.last_quarter_revenue)} highlight="green" />
      </div>

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
