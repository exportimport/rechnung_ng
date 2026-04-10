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
