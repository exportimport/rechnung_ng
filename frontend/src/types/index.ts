// All types use snake_case to match the backend JSON wire format directly.

export interface PriceEntry {
  amount: string; // Decimal serialised as string
  valid_from: string; // ISO date
}

export interface Plan {
  id: number;
  name: string;
  price_history: PriceEntry[];
  current_price?: number | null;
}

export interface PlanCreate {
  name: string;
  initial_price: string;
  valid_from: string;
}

export interface AddPriceRequest {
  amount: string;
  valid_from: string;
}

export interface Customer {
  id: number;
  vorname: string;
  nachname: string;
  street: string;
  house_number: string;
  postcode: string;
  city: string;
  iban: string;
  email: string;
  comment?: string | null;
}

export interface CustomerCreate {
  vorname: string;
  nachname: string;
  street: string;
  house_number: string;
  postcode: string;
  city: string;
  iban: string;
  email: string;
  comment?: string | null;
}

export type BillingCycle = "monthly" | "quarterly";
export type ContractStatus = "active" | "not_yet_active" | "cancelled";

export interface Contract {
  id: number;
  customer_id: number;
  plan_id: number;
  start_date: string;
  end_date?: string | null;
  reference?: string | null;
  billing_cycle: BillingCycle;
  scan_file?: string | null;
  cancellation_pdf?: string | null;
  comment?: string | null;
  status: ContractStatus;
  customer_name: string;
  plan_name: string;
  current_price?: number | null;
}

export interface ContractCreate {
  customer_id: number;
  plan_id: number;
  start_date: string;
  end_date?: string | null;
  reference?: string | null;
  billing_cycle: BillingCycle;
  comment?: string | null;
}

export interface MailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
}

export type InvoiceStatus = "draft" | "sent";

export interface Invoice {
  id: number;
  contract_id: number;
  customer_id: number;
  invoice_number: string;
  year: number;
  month: number;
  amount: number;
  period_start: string;
  period_end: string;
  status: InvoiceStatus;
  pdf_path?: string | null;
  mail_template?: string | null;
  created_at: string;
  sent_at?: string | null;
}
