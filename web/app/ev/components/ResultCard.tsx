"use client";

import type { EVResponse } from "../types";

export default function ResultCard({ result }: { result: EVResponse | null }) {
  if (!result) {
    return null;
  }

  return (
    <div className="mt-6 p-4 border rounded bg-gray-50">
      <h2 className="font-semibold text-lg mb-3">EV Result</h2>

      <div className="space-y-1 text-sm">
        <div><strong>Model Probability:</strong> {result.p_model.toFixed(4)}</div>
        <div><strong>Fair Price:</strong> {result.fair_price.toFixed(4)}</div>
        <div><strong>Market Price:</strong> {result.market_price.toFixed(4)}</div>
        <div><strong>Fee Cost:</strong> {result.fee_cost.toFixed(4)}</div>
        <div><strong>Edge (Raw):</strong> {result.edge_raw.toFixed(4)}</div>
        <div><strong>Edge (After Fees):</strong> {result.edge_after_fees.toFixed(4)}</div>
        <div><strong>EV per Contract:</strong> {result.ev_per_contract.toFixed(4)}</div>
      </div>
    </div>
  );
}
