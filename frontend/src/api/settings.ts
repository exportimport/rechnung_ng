import { api } from "./client";

export interface Settings {
  company: {
    name: string;
    address: string;
    email: string;
    phone: string;
    tax_id: string;
    bank_name: string;
    iban: string;
    bic: string;
  };
  smtp: {
    host: string;
    port: number;
    username: string;
    use_tls: boolean;
    use_ssl: boolean;
    sender_name: string;
    sender_email: string;
  };
  invoice: {
    number_format: string;
    payment_terms_days: number;
    vat_rate: number;
    currency: string;
  };
}

export const settingsApi = {
  get: () => api.get<Settings>("/settings"),
  update: (body: Settings) => api.put<Settings>("/settings", body),
};
