import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { plansApi } from "../api/plans";
import { TextField, DateField } from "../components/FormFields";
import { formatEuro, formatDate } from "../lib/format";

interface CreateFields {
  name: string;
  initial_price: string;
  valid_from: string;
}

interface AddPriceFields {
  amount: string;
  valid_from: string;
}

export default function PlanForm() {
  const { id } = useParams<{ id: string }>();
  const isNew = id === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: plan } = useQuery({
    queryKey: ["plans", Number(id)],
    queryFn: () => plansApi.get(Number(id)),
    enabled: !isNew,
  });

  const form = useForm<CreateFields>({
    defaultValues: { name: "", initial_price: "", valid_from: "" },
  });

  const addPriceForm = useForm<AddPriceFields>({
    defaultValues: { amount: "", valid_from: "" },
  });

  useEffect(() => {
    if (plan) form.reset({ name: plan.name });
  }, [plan, form]);

  const createMutation = useMutation({
    mutationFn: plansApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      toast.success("Tarif erstellt");
      navigate("/plans");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateMutation = useMutation({
    mutationFn: (data: { name: string }) => plansApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      toast.success("Tarif gespeichert");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const addPriceMutation = useMutation({
    mutationFn: (data: AddPriceFields) => plansApi.addPrice(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans", Number(id)] });
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      toast.success("Preis hinzugefügt");
      addPriceForm.reset();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function onSubmit(data: CreateFields) {
    if (isNew) {
      createMutation.mutate(data);
    } else {
      updateMutation.mutate({ name: data.name });
    }
  }

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate("/plans")} className="text-sm text-gray-500 hover:text-gray-700">
          ← Zurück
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">
          {isNew ? "Neuer Tarif" : "Tarif bearbeiten"}
        </h1>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 bg-white p-6 rounded-lg border border-violet-100 shadow-sm">
        <TextField
          label="Tarifname"
          registration={form.register("name", { required: "Pflichtfeld" })}
          error={form.formState.errors.name}
          required
        />
        {isNew && (
          <>
            <TextField
              label="Startpreis (Brutto inkl. 19% MwSt)"
              registration={form.register("initial_price", { required: "Pflichtfeld" })}
              error={form.formState.errors.initial_price}
              required
            />
            <DateField
              label="Gültig ab"
              registration={form.register("valid_from", { required: "Pflichtfeld" })}
              error={form.formState.errors.valid_from}
              required
            />
          </>
        )}
        <div className="pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-violet-500 text-white text-sm font-medium rounded-md hover:bg-violet-600"
          >
            {isNew ? "Erstellen" : "Speichern"}
          </button>
        </div>
      </form>

      {!isNew && plan && (
        <div className="mt-8">
          <h2 className="text-lg font-medium text-gray-900 mb-3">Preisverlauf</h2>
          <div className="bg-white rounded-lg border border-violet-100 divide-y divide-gray-100 mb-4 shadow-sm">
            {plan.price_history.map((entry, i) => (
              <div key={i} className="flex justify-between px-4 py-3 text-sm">
                <span className="text-gray-500">ab {formatDate(entry.valid_from)}</span>
                <span className="font-medium text-gray-900">
                  {formatEuro(parseFloat(entry.amount))}
                </span>
              </div>
            ))}
          </div>

          <h3 className="text-sm font-medium text-gray-700 mb-3">Neuen Preis hinzufügen</h3>
          <form
            onSubmit={addPriceForm.handleSubmit((d) => addPriceMutation.mutate(d))}
            className="flex gap-3 items-end bg-white p-4 rounded-lg border border-violet-100 shadow-sm"
          >
            <div className="flex-1">
              <TextField
                label="Betrag (Brutto)"
                registration={addPriceForm.register("amount", { required: "Pflichtfeld" })}
                error={addPriceForm.formState.errors.amount}
                required
              />
            </div>
            <div className="flex-1">
              <DateField
                label="Gültig ab"
                registration={addPriceForm.register("valid_from", { required: "Pflichtfeld" })}
                error={addPriceForm.formState.errors.valid_from}
                required
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-violet-500 text-white text-sm font-medium rounded-md hover:bg-violet-600 h-[38px]"
            >
              Hinzufügen
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
