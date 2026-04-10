import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { mailTemplatesApi } from "../api/mailTemplates";
import type { MailTemplate } from "../types";

const VARIABLES = [
  "{{ customer.vorname }}",
  "{{ customer.nachname }}",
  "{{ customer.email }}",
  "{{ invoice.invoice_number }}",
  '{{ "%.2f"|format(invoice.amount) }}',
  "{{ invoice.period_start }}",
  "{{ invoice.period_end }}",
];

interface FormFields {
  subject: string;
  body: string;
}

export default function MailTemplates() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string>("default");

  const { data: templates = [] } = useQuery({
    queryKey: ["mail-templates"],
    queryFn: mailTemplatesApi.list,
  });

  const current = templates.find((t) => t.id === selected);

  const form = useForm<FormFields>({ defaultValues: { subject: "", body: "" } });

  useEffect(() => {
    if (current) form.reset({ subject: current.subject, body: current.body });
  }, [current, form]);

  const updateMutation = useMutation({
    mutationFn: (data: FormFields) => mailTemplatesApi.update(selected, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mail-templates"] });
      toast.success("Vorlage gespeichert");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Mail-Vorlagen</h1>

      <div className="flex gap-6">
        <aside className="w-48 shrink-0">
          <nav className="space-y-0.5">
            {templates.map((t: MailTemplate) => (
              <button
                key={t.id}
                onClick={() => setSelected(t.id)}
                className={[
                  "w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  selected === t.id
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-600 hover:bg-gray-100",
                ].join(" ")}
              >
                {t.name}
              </button>
            ))}
          </nav>
        </aside>

        <div className="flex-1 max-w-xl">
          {current ? (
            <form
              onSubmit={form.handleSubmit((d) => updateMutation.mutate(d))}
              className="space-y-4 bg-white p-6 rounded-lg border border-gray-200"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Betreff</label>
                <input
                  type="text"
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  {...form.register("subject", { required: true })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nachricht</label>
                <textarea
                  rows={12}
                  className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  {...form.register("body", { required: true })}
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
              >
                Speichern
              </button>
            </form>
          ) : (
            <p className="text-gray-400">Vorlage auswählen</p>
          )}
        </div>

        <div className="w-48 shrink-0">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Verfügbare Variablen
          </h3>
          <ul className="space-y-1">
            {VARIABLES.map((v) => (
              <li key={v}>
                <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-700 break-all">
                  {v}
                </code>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
