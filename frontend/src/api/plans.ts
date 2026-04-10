import { api } from "./client";
import type { AddPriceRequest, Plan, PlanCreate } from "../types";

export const plansApi = {
  list: () => api.get<Plan[]>("/plans"),
  get: (id: number) => api.get<Plan>(`/plans/${id}`),
  create: (data: PlanCreate) => api.post<Plan>("/plans", data),
  update: (id: number, data: { name: string }) => api.put<Plan>(`/plans/${id}`, data),
  addPrice: (id: number, data: AddPriceRequest) =>
    api.post<Plan>(`/plans/${id}/price`, data),
  delete: (id: number) => api.delete<void>(`/plans/${id}`),
};
