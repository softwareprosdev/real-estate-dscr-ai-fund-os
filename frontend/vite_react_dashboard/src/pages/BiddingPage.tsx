import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import MetricCard from "../components/MetricCard";

const DEFAULTS = {
  property_id: "PROP_0001",
  source: "auction",
  ask_price: 92000,
  estimated_monthly_rent: 1050,
  rehab_cost: 15000,
  arv: 115000,
  competition_saturation: 0.55,
  days_on_market: 21,
  min_profit_margin: 0.08,
  loan_rate: 0.079,
  ltv: 0.75,
};

export default function BiddingPage() {
  const [form, setForm] = useState(DEFAULTS);
  const mutation = useMutation({
    mutationFn: (data: typeof DEFAULTS) => api.post<any>("/bidding/optimize", data),
  });

  const r = mutation.data;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-green-400">Bid Optimizer</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Object.entries(DEFAULTS).map(([key, val]) => (
          <label key={key} className="flex flex-col gap-1">
            <span className="text-xs text-gray-400 uppercase">{key.replace(/_/g, " ")}</span>
            {typeof val === "number" ? (
              <input
                type="number"
                step="any"
                className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
                value={(form as any)[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))}
              />
            ) : (
              <input
                type="text"
                className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
                value={(form as any)[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            )}
          </label>
        ))}
      </div>

      <button
        onClick={() => mutation.mutate(form)}
        disabled={mutation.isPending}
        className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded font-bold disabled:opacity-50"
      >
        {mutation.isPending ? "Optimizing..." : "Optimize Bid"}
      </button>

      {r && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <MetricCard label="Ask Price" value={`$${r.current_ask.toLocaleString()}`} />
            <MetricCard label="Max Allowable Bid" value={`$${r.max_allowable_bid.toLocaleString()}`} variant="warn" />
            <MetricCard label="Recommended Bid" value={`$${r.recommended_bid.toLocaleString()}`} variant="good" />
            <MetricCard label="Win Probability" value={`${(r.win_probability * 100).toFixed(0)}%`} />
            <MetricCard label="Expected Profit" value={`$${r.expected_profit_at_bid.toLocaleString()}`} />
            <MetricCard label="Expected Value" value={`$${r.expected_value.toLocaleString()}`} />
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-4">
            <p className="text-xs text-gray-400 mb-2">STRATEGY: <span className="text-white font-bold uppercase">{r.bid_strategy.replace(/_/g, " ")}</span></p>
            <ul>{r.reasoning.map((t: string, i: number) => <li key={i} className="text-sm text-gray-300">• {t}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  );
}
