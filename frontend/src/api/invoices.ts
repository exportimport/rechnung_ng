import { api } from "./client";
import type { Invoice, InvoiceStatus } from "../types";

export const invoicesApi = {
  list: (params?: { year?: number; month?: number; status?: InvoiceStatus }) => {
    const q = new URLSearchParams();
    if (params?.year) q.set("year", String(params.year));
    if (params?.month) q.set("month", String(params.month));
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api.get<Invoice[]>(`/invoices${qs ? `?${qs}` : ""}`);
  },
  get: (id: number) => api.get<Invoice>(`/invoices/${id}`),
  generate: (year: number, month: number) =>
    api.post<Invoice[]>("/invoices/generate", { year, month }),
  send: (id: number, template_id: string) =>
    api.post<Invoice>(`/invoices/${id}/send`, { template_id }),
  sendBatch: (year: number, month: number) =>
    api.post<Invoice[]>("/invoices/send-batch", { year, month }),
  pdfUrl: (id: number) => `/api/v1/invoices/${id}/pdf`,
};
