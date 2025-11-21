// app/ev/types.ts

export type Side = "home_yes" | "home_no";

export type EVResponse = {
  p_model: number;
  fair_price: number;
  market_price: number;
  fee_cost: number;
  edge_raw: number;
  edge_after_fees: number;
  ev_per_contract: number;
};
