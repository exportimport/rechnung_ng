import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { contractsApi } from "../api/contracts";
import { customersApi } from "../api/customers";
import { plansApi } from "../api/plans";
import { TextField, TextAreaField, SelectField, DateField } from "../components/FormFields";
import { formatEuro } from "../lib/format";
import type { ContractCreate } from "../types";

export default function ContractForm() {
  const { id } = useParams<{ id: string }>();
  const isNew = id === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [cancelDate, setCancelDate] = useState("");
  const [showCancelForm, setShowCancelForm] = useState(false);

  const { data: contract } = useQuery({
    queryKey: ["contracts", Number(id)],
    queryFn: () => contractsApi.get(Number(id)),
    enabled: !isNew,
  });

  const { data: customers = [] } = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersApi.list(),
  });

  const { data: plans = [] } = useQuery({
    queryKey: ["plans"],
    queryFn: () => plansApi.list(),
  });

  const form = useForm<ContractCreate & { end_date_str: string }>({
    defaultValues: {
      customer_id: 0,
      plan_id: 0,
      start_date: "",
      end_date: null,
      reference: "",
      billing_cycle: "monthly",
      comment: "",
    },
  });

  useEffect(() => {
    if (contract) {
      form.reset({
        customer_id: contract.customer_id,
        plan_id: contract.plan_id,
        start_date: contract.start_date,
        end_date: contract.end_date ?? null,
        reference: contract.reference ?? "",
        billing_cycle: contract.billing_cycle,
        comment: contract.comment ?? "",
      });
    }
  }, [contract, form]);

  const createMutation = useMutation({
    mutationFn: (data: ContractCreate) => contractsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      toast.success("Vertrag erstellt");
      navigate("/contracts");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateMutation = useMutation({
    mutationFn: (data: ContractCreate) => contractsApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      toast.success("Vertrag gespeichert");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => contractsApi.uploadScan(Number(id), file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts", Number(id)] });
      toast.success("Scan hochgeladen");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const cancelMutation = useMutation({
    mutationFn: (date: string) => contractsApi.cancel(Number(id), date),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts", Number(id)] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      toast.success("Vertrag gekündigt");
      setShowCancelForm(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function onSubmit(data: ContractCreate) {
    const payload: ContractCreate = {
      ...data,
      customer_id: Number(data.customer_id),
      plan_id: Number(data.plan_id),
      end_date: data.end_date || null,
      reference: data.reference || null,
      comment: data.comment || null,
    };
    if (isNew) {
      createMutation.mutate(payload);
    } else {
      updateMutation.mutate(payload);
    }
  }

  const customerOptions = customers.map((c) => ({
    value: c.id,
    label: `${c.nachname}, ${c.vorname}`,
  }));

  const planOptions = plans.map((p) => ({
    value: p.id,
    label: `${p.name}${p.current_price != null ? ` (${formatEuro(p.current_price)})` : ""}`,
  }));

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate("/contracts")}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Zurück
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">
          {isNew ? "Neuer Vertrag" : "Vertrag bearbeiten"}
        </h1>
      </div>

      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4 bg-white p-6 rounded-lg border border-gray-200"
      >
        <SelectField
          label="Kunde"
          registration={form.register("customer_id", { required: "Pflichtfeld", valueAsNumber: true })}
          error={form.formState.errors.customer_id}
          options={customerOptions}
          required
        />
        <SelectField
          label="Tarif"
          registration={form.register("plan_id", { required: "Pflichtfeld", valueAsNumber: true })}
          error={form.formState.errors.plan_id}
          options={planOptions}
          required
        />
        <div className="grid grid-cols-2 gap-4">
          <DateField
            label="Vertragsbeginn"
            registration={form.register("start_date", { required: "Pflichtfeld" })}
            error={form.formState.errors.start_date}
            required
          />
          <DateField
            label="Vertragsende (optional)"
            registration={form.register("end_date")}
          />
        </div>
        <TextField
          label="Referenz / Aktenzeichen (optional)"
          registration={form.register("reference")}
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Abrechnungszyklus</label>
          <div className="flex gap-4">
            {(["monthly", "quarterly"] as const).map((v) => (
              <label key={v} className="flex items-center gap-2 text-sm text-gray-700">
                <input type="radio" value={v} {...form.register("billing_cycle")} />
                {v === "monthly" ? "Monatlich" : "Quartalsweise"}
              </label>
            ))}
          </div>
        </div>
        <TextAreaField
          label="Kommentar (optional)"
          registration={form.register("comment")}
          rows={2}
        />
        <div className="pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
          >
            {isNew ? "Erstellen" : "Speichern"}
          </button>
        </div>
      </form>

      {!isNew && contract && (
        <div className="mt-6 space-y-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h2 className="text-sm font-medium text-gray-900 mb-3">Vertragsscan</h2>
            {contract.scan_file ? (
              <a
                href={contractsApi.scanUrl(contract.id)}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-indigo-600 hover:underline"
              >
                Scan herunterladen (PDF)
              </a>
            ) : (
              <p className="text-sm text-gray-400 mb-2">Kein Scan vorhanden.</p>
            )}
            <div className="mt-2">
              <input
                type="file"
                accept=".pdf"
                ref={fileRef}
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadMutation.mutate(file);
                }}
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                {contract.scan_file ? "Scan ersetzen" : "Scan hochladen"}
              </button>
            </div>
          </div>

          {contract.status !== "cancelled" && (
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h2 className="text-sm font-medium text-gray-900 mb-3">Kündigung</h2>
              {!showCancelForm ? (
                <button
                  type="button"
                  onClick={() => setShowCancelForm(true)}
                  className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
                >
                  Vertrag kündigen
                </button>
              ) : (
                <div className="flex gap-3 items-end">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Kündigungsdatum</label>
                    <input
                      type="date"
                      value={cancelDate}
                      onChange={(e) => setCancelDate(e.target.value)}
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => cancelDate && cancelMutation.mutate(cancelDate)}
                    className="px-3 py-2 text-sm text-white bg-red-600 rounded-md hover:bg-red-700"
                  >
                    Bestätigen
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCancelForm(false)}
                    className="px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Abbrechen
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
