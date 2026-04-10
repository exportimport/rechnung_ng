import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { customersApi } from "../api/customers";
import { TextField, TextAreaField } from "../components/FormFields";
import type { CustomerCreate } from "../types";

export default function CustomerForm() {
  const { id } = useParams<{ id: string }>();
  const isNew = id === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: customer } = useQuery({
    queryKey: ["customers", Number(id)],
    queryFn: () => customersApi.get(Number(id)),
    enabled: !isNew,
  });

  const form = useForm<CustomerCreate>({
    defaultValues: {
      vorname: "",
      nachname: "",
      adresse: "",
      iban: "",
      email: "",
      comment: "",
    },
  });

  useEffect(() => {
    if (customer) form.reset(customer);
  }, [customer, form]);

  const createMutation = useMutation({
    mutationFn: customersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Kunde erstellt");
      navigate("/customers");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateMutation = useMutation({
    mutationFn: (data: CustomerCreate) => customersApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Kunde gespeichert");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const deleteMutation = useMutation({
    mutationFn: () => customersApi.delete(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Kunde gelöscht");
      navigate("/customers");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function onSubmit(data: CustomerCreate) {
    if (isNew) {
      createMutation.mutate(data);
    } else {
      updateMutation.mutate(data);
    }
  }

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate("/customers")}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Zurück
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">
          {isNew ? "Neuer Kunde" : "Kunde bearbeiten"}
        </h1>
      </div>

      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4 bg-white p-6 rounded-lg border border-gray-200"
      >
        <div className="grid grid-cols-2 gap-4">
          <TextField
            label="Vorname"
            registration={form.register("vorname", { required: "Pflichtfeld" })}
            error={form.formState.errors.vorname}
            required
          />
          <TextField
            label="Nachname"
            registration={form.register("nachname", { required: "Pflichtfeld" })}
            error={form.formState.errors.nachname}
            required
          />
        </div>
        <TextAreaField
          label="Adresse"
          registration={form.register("adresse", { required: "Pflichtfeld" })}
          error={form.formState.errors.adresse}
          required
          rows={3}
        />
        <TextField
          label="IBAN"
          registration={form.register("iban", { required: "Pflichtfeld" })}
          error={form.formState.errors.iban}
          required
        />
        <TextField
          label="E-Mail"
          type="email"
          registration={form.register("email", { required: "Pflichtfeld" })}
          error={form.formState.errors.email}
          required
        />
        <TextAreaField
          label="Kommentar (optional)"
          registration={form.register("comment")}
          rows={2}
        />

        <div className="flex items-center justify-between pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
          >
            {isNew ? "Erstellen" : "Speichern"}
          </button>
          {!isNew && (
            <button
              type="button"
              onClick={() => {
                if (window.confirm("Kunde wirklich löschen?")) deleteMutation.mutate();
              }}
              className="px-4 py-2 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
            >
              Löschen
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
