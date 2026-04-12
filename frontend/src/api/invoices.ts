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
  generate: (
    year: number,
    month: number,
    onProgress: (current: number, total: number) => void,
  ): Promise<number> =>
    new Promise(async (resolve, reject) => {
      try {
        const res = await fetch("/api/v1/invoices/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ year, month }),
        });
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = JSON.parse(line.slice(6));
            if (data.done) resolve(data.count);
            else onProgress(data.current, data.total);
          }
        }
      } catch (e) {
        reject(e);
      }
    }),
  send: (id: number, template_id: string) =>
    api.post<Invoice>(`/invoices/${id}/send`, { template_id }),
  sendBatch: (year: number, month: number) =>
    api.post<Invoice[]>("/invoices/send-batch", { year, month }),
  delete: (id: number) => api.delete(`/invoices/${id}`),
  bulkDelete: (ids: number[]) => api.post<void>("/invoices/bulk-delete", { ids }),
  pdfUrl: (id: number) => `/api/v1/invoices/${id}/pdf`,
};
