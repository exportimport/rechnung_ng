import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { settingsApi, Settings } from "../api/settings";
import { ApiError } from "../api/client";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-lg p-6">
      <h2 className="text-lg font-semibold text-violet-800 mb-4">{title}</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  hint,
  full,
}: {
  label: string;
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  hint?: string;
  full?: boolean;
}) {
  return (
    <div className={full ? "sm:col-span-2" : ""}>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-white/60 bg-white/70 backdrop-blur-sm shadow-sm px-3 py-2 text-sm focus:outline-none focus:border-violet-400 focus:ring-1 focus:ring-violet-400"
      />
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={[
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none",
          checked ? "bg-violet-500" : "bg-gray-300",
        ].join(" ")}
      >
        <span
          className={[
            "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-6" : "translate-x-1",
          ].join(" ")}
        />
      </button>
      <span className="text-sm text-gray-700">{label}</span>
    </div>
  );
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["settings"], queryFn: settingsApi.get });
  const [form, setForm] = useState<Settings | null>(null);
  const [toast, setToast] = useState<{ ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    if (data) setForm(structuredClone(data));
  }, [data]);

  const mutation = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: (updated) => {
      queryClient.setQueryData(["settings"], updated);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setToast({ ok: true, msg: "Einstellungen gespeichert" });
      setTimeout(() => setToast(null), 3000);
    },
    onError: (e) => {
      setToast({ ok: false, msg: e instanceof ApiError ? e.message : "Fehler beim Speichern" });
      setTimeout(() => setToast(null), 4000);
    },
  });

  if (isLoading || !form) {
    return <div className="text-violet-700 animate-pulse">Lade Einstellungen…</div>;
  }

  const set = <K extends keyof Settings>(section: K) =>
    (field: keyof Settings[K]) =>
    (value: string) => {
      setForm((f) => {
        if (!f) return f;
        return { ...f, [section]: { ...f[section], [field]: value } };
      });
    };

  const setNum = <K extends keyof Settings>(section: K) =>
    (field: keyof Settings[K]) =>
    (value: string) => {
      setForm((f) => {
        if (!f) return f;
        return { ...f, [section]: { ...f[section], [field]: Number(value) } };
      });
    };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-violet-900">Einstellungen</h1>

      <Section title="Unternehmen">
        <Field label="Firmenname" value={form.company.name} onChange={set("company")("name")} />
        <Field label="E-Mail" value={form.company.email} onChange={set("company")("email")} />
        <Field
          label="Adresse"
          value={form.company.address}
          onChange={set("company")("address")}
          full
        />
        <Field label="Telefon" value={form.company.phone} onChange={set("company")("phone")} />
        <Field label="Steuernummer / USt-ID" value={form.company.tax_id} onChange={set("company")("tax_id")} />
        <Field label="Bank" value={form.company.bank_name} onChange={set("company")("bank_name")} />
        <Field label="IBAN" value={form.company.iban} onChange={set("company")("iban")} />
        <Field label="BIC" value={form.company.bic} onChange={set("company")("bic")} />
      </Section>

      <Section title="Rechnungen">
        <Field
          label="Nummernformat"
          value={form.invoice.number_format}
          onChange={set("invoice")("number_format")}
          hint="Variablen: {customer_id} {contract_id} {year} {month:02d} {seq:04d}"
          full
        />
        <Field
          label="Zahlungsziel (Tage)"
          value={form.invoice.payment_terms_days}
          onChange={setNum("invoice")("payment_terms_days")}
          type="number"
        />
        <Field
          label="MwSt-Satz"
          value={form.invoice.vat_rate}
          onChange={setNum("invoice")("vat_rate")}
          type="number"
          hint="z.B. 0.19 für 19%"
        />
        <Field label="Währung" value={form.invoice.currency} onChange={set("invoice")("currency")} />
      </Section>

      <Section title="E-Mail / SMTP">
        <Field label="SMTP-Host" value={form.smtp.host} onChange={set("smtp")("host")} />
        <Field label="Port" value={form.smtp.port} onChange={setNum("smtp")("port")} type="number" />
        <Field label="Benutzername" value={form.smtp.username} onChange={set("smtp")("username")} />
        <Field
          label="Absender-Name"
          value={form.smtp.sender_name}
          onChange={set("smtp")("sender_name")}
        />
        <Field
          label="Absender-E-Mail"
          value={form.smtp.sender_email}
          onChange={set("smtp")("sender_email")}
        />
        <div className="sm:col-span-2 flex gap-6 mt-1">
          <Toggle
            label="STARTTLS (Port 587)"
            checked={form.smtp.use_tls}
            onChange={(v) => setForm((f) => f && { ...f, smtp: { ...f.smtp, use_tls: v } })}
          />
          <Toggle
            label="SSL/TLS (Port 465)"
            checked={form.smtp.use_ssl}
            onChange={(v) => setForm((f) => f && { ...f, smtp: { ...f.smtp, use_ssl: v } })}
          />
        </div>
        <p className="sm:col-span-2 text-xs text-gray-500">
          Das SMTP-Passwort wird über die <code>.env</code>-Datei konfiguriert und hier nicht angezeigt.
        </p>
      </Section>

      <div className="flex justify-end">
        <button
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
          className="px-6 py-2.5 bg-violet-500 hover:bg-violet-600 disabled:opacity-50 text-white font-medium rounded-full shadow transition-colors"
        >
          {mutation.isPending ? "Speichern…" : "Speichern"}
        </button>
      </div>

      {toast && (
        <div
          className={[
            "fixed bottom-6 right-6 px-4 py-3 rounded-2xl shadow-lg text-sm font-medium text-white",
            toast.ok ? "bg-green-500" : "bg-red-500",
          ].join(" ")}
        >
          {toast.msg}
        </div>
      )}
    </div>
  );
}
