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
      <h1 className="text-2xl font-bold text-violet-800 mb-6">Mail-Vorlagen</h1>

      <div className="flex gap-6">
        <aside className="w-48 shrink-0">
          <nav className="space-y-1">
            {templates.map((t: MailTemplate) => (
              <button
                key={t.id}
                onClick={() => setSelected(t.id)}
                className={[
                  "w-full text-left px-4 py-2.5 rounded-full text-sm font-medium transition-all",
                  selected === t.id
                    ? "bg-white/70 text-violet-700 shadow-sm backdrop-blur-sm"
                    : "text-violet-900/60 hover:bg-white/40 hover:text-violet-800",
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
              className="space-y-4 bg-white/70 backdrop-blur-sm p-6 rounded-2xl border border-white/60 shadow-lg"
            >
              <div>
                <label className="block text-sm font-medium text-violet-900/80 mb-1">Betreff</label>
                <input
                  type="text"
                  className="block w-full rounded-xl border border-white/60 bg-white/70 backdrop-blur-sm px-3 py-2 text-sm shadow-sm focus:border-violet-400 focus:outline-none focus:ring-1 focus:ring-violet-400"
                  {...form.register("subject", { required: true })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-violet-900/80 mb-1">Nachricht</label>
                <textarea
                  rows={12}
                  className="block w-full rounded-xl border border-white/60 bg-white/70 backdrop-blur-sm px-3 py-2 text-sm font-mono shadow-sm focus:border-violet-400 focus:outline-none focus:ring-1 focus:ring-violet-400"
                  {...form.register("body", { required: true })}
                />
              </div>
              <button
                type="submit"
                className="px-5 py-2 bg-violet-500 text-white text-sm font-medium rounded-full hover:bg-violet-600 shadow-sm transition-colors"
              >
                Speichern
              </button>
            </form>
          ) : (
            <p className="text-violet-400">Vorlage auswählen</p>
          )}
        </div>

        <div className="w-48 shrink-0">
          <h3 className="text-xs font-semibold text-violet-600 uppercase tracking-wider mb-3">
            Verfügbare Variablen
          </h3>
          <ul className="space-y-1.5">
            {VARIABLES.map((v) => (
              <li key={v}>
                <code className="text-xs bg-white/60 backdrop-blur-sm px-2 py-1 rounded-full text-violet-700 break-all border border-white/60">
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
