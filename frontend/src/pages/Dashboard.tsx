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

  if (isLoading) return <p className="text-gray-500">Wird geladen…</p>;
  if (!data) return null;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 mb-8 max-w-lg">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Offene Rechnungen</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data.draft_count}</p>
        </div>
        <div
          className={[
            "rounded-lg border p-4",
            data.overdue_count > 0
              ? "bg-red-50 border-red-200"
              : "bg-white border-gray-200",
          ].join(" ")}
        >
          <p className="text-sm text-gray-500">Überfällig</p>
          <p
            className={[
              "text-3xl font-bold mt-1",
              data.overdue_count > 0 ? "text-red-700" : "text-gray-900",
            ].join(" ")}
          >
            {data.overdue_count}
          </p>
        </div>
      </div>

      {data.draft_invoices.length === 0 ? (
        <p className="text-gray-400">Keine offenen Rechnungen.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Rechnungsnummer", "Kunde", "Betrag", "Erstellt", "Fällig", ""].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.draft_invoices.map((inv) => (
                <tr key={inv.id} className={inv.overdue ? "bg-red-50" : ""}>
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">
                    {inv.invoice_number}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{inv.customer_name}</td>
                  <td className="px-4 py-3 text-gray-700">{formatEuro(inv.amount)}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(inv.created_at)}</td>
                  <td
                    className={[
                      "px-4 py-3",
                      inv.overdue ? "text-red-700 font-medium" : "text-gray-500",
                    ].join(" ")}
                  >
                    {formatDate(inv.due_date)}
                    {inv.overdue && " ⚠"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() =>
                        sendMutation.mutate({ id: inv.id, template_id: "auto" })
                      }
                      className="text-xs text-indigo-600 hover:underline"
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
