import { api } from "./client";
import type { MailTemplate } from "../types";

export const mailTemplatesApi = {
  list: () => api.get<MailTemplate[]>("/mail-templates"),
  get: (id: string) => api.get<MailTemplate>(`/mail-templates/${id}`),
  update: (id: string, data: { subject: string; body: string }) =>
    api.put<MailTemplate>(`/mail-templates/${id}`, data),
};
