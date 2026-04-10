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
  draft_invoices: DashboardInvoice[];
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

      <div className="grid grid-cols-2 gap-4 mb-8 max-w-lg">
        <div className="bg-sky-100/60 backdrop-blur-sm rounded-2xl border border-white/60 shadow-lg p-5">
          <p className="text-sm text-sky-600 font-medium">Offene Rechnungen</p>
          <p className="text-4xl font-bold text-sky-700 mt-1">{data.draft_count}</p>
        </div>
        <div
          className={[
            "backdrop-blur-sm rounded-2xl border border-white/60 shadow-lg p-5",
            data.overdue_count > 0 ? "bg-red-100/60" : "bg-white/50",
          ].join(" ")}
        >
          <p className="text-sm text-gray-500 font-medium">Überfällig</p>
          <p className={["text-4xl font-bold mt-1", data.overdue_count > 0 ? "text-red-600" : "text-gray-700"].join(" ")}>
            {data.overdue_count}
          </p>
        </div>
      </div>

      {data.draft_invoices.length === 0 ? (
        <p className="text-violet-400">Keine offenen Rechnungen.</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/60 bg-white/70 backdrop-blur-sm shadow-lg">
          <table className="min-w-full divide-y divide-white/40 text-sm">
            <thead className="bg-white/40">
              <tr>
                {["Rechnungsnummer", "Kunde", "Betrag", "Erstellt", "Fällig", ""].map((h) => (
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
