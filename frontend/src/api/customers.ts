import { api } from "./client";
import type { Customer, CustomerCreate } from "../types";

export const customersApi = {
  list: (q?: string) =>
    api.get<Customer[]>(`/customers${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  get: (id: number) => api.get<Customer>(`/customers/${id}`),
  create: (data: CustomerCreate) => api.post<Customer>("/customers", data),
  update: (id: number, data: CustomerCreate) =>
    api.put<Customer>(`/customers/${id}`, data),
  delete: (id: number) => api.delete<void>(`/customers/${id}`),
};
