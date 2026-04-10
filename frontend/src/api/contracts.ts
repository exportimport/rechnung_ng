import { api } from "./client";
import type { Contract, ContractCreate, ContractStatus } from "../types";

export const contractsApi = {
  list: (status?: ContractStatus) =>
    api.get<Contract[]>(`/contracts${status ? `?status=${status}` : ""}`),
  get: (id: number) => api.get<Contract>(`/contracts/${id}`),
  create: (data: ContractCreate) => api.post<Contract>("/contracts", data),
  update: (id: number, data: ContractCreate) =>
    api.put<Contract>(`/contracts/${id}`, data),
  delete: (id: number) => api.delete<void>(`/contracts/${id}`),
  cancel: (id: number, end_date: string) =>
    api.post<Contract>(`/contracts/${id}/cancel`, { end_date }),
  uploadScan: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<Contract>(`/contracts/${id}/scan`, fd);
  },
  scanUrl: (id: number) => `/api/v1/contracts/${id}/scan`,
  cancellationPdfUrl: (id: number) => `/api/v1/contracts/${id}/cancellation-pdf`,
};
