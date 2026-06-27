import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import MetricCard from "../components/MetricCard";

const DEFAULTS = {
  underwriting_input: {
    property_id: "PROP_0001",
    purchase_price: 85000,
    arv: 115000,
    estimated_monthly_rent: 1050,
    section_8_rent: 1150,
    rehab_cost_estimate: 15000,
    loan_rate: 0.079,
    ltv: 0.75,
    vacancy_rate: 0.08,
    property_mgmt_rate: 0.10,
    maintenance_rate: 0.05,
    capex_rate: 0.05,
  },
  lender_input: {
    property_id: "PROP_0001",
    lender_id: "all",
    dscr_base: 1.35,
    dscr_stress: 1.12,
    ltv: 0.75,
    loan_amount: 63750,
    property_condition_score: 0.50,
    zip_code: "38118",
    zip_liquidity_index: 0.65,
    rehab_risk_score: 0.20,
    year_built: 1978,
  },
  sqft: 1450,
  condition: "fair",
  property_type: "sfr",
  year_built: 1978,
  zip_code: "38118",
  state: "TN",
  market_investor_activity: 0.45,
  market_liquidity_index: 0.65,
  days_on_market: 45,
  competition_saturation: 0.40,
  macro_regime: "expansion",
  available_cash: 2000000,
  zip_exposure_pct: {},
};

export default function DealDecisionPage() {
  const [form] = useState(DEFAULTS);
  const mutation = useMutation({
    mutationFn: (data: typeof DEFAULTS) => api.post<any>("/decision/analyze", data),
  });

  const d = mutation.data;
  const decisionColor = d?.decision === "BUY" || d?.decision === "STRONG_BUY"
    ? "text-green-400"
    : d?.decision === "CONDITIONAL"
    ? "text-yellow-400"
    : "text-red-400";

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-green-400">Full Acquisition Decision</h1>
      <p className="text-gray-400 text-sm">Runs underwriting + lender simulation + rehab estimate + portfolio constraints → BUY/REJECT/HOLD</p>

      <button
        onClick={() => mutation.mutate(form)}
        disabled={mutation.isPending}
        className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded font-bold disabled:opacity-50"
      >
        {mutation.isPending ? "Analyzing..." : "Run Full Decision (Memphis SFR Sample)"}
      </button>

      {d && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <span className={`text-4xl font-black ${decisionColor}`}>{d.decision}</span>
              <div>
                <p className="text-gray-400 text-sm">Confidence: <span className="text-white font-bold">{(d.confidence * 100).toFixed(0)}%</span></p>
                <p className="text-gray-400 text-sm">Position Size: <span className="text-white font-bold">${d.position_size?.toLocaleString()}</span></p>
                <p className="text-gray-400 text-sm">Recommended Bid: <span className="text-white font-bold">${d.recommended_bid?.toLocaleString()}</span></p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
              <MetricCard label="DSCR Base" value={d.dscr_summary?.dscr_base?.toFixed(3)} />
              <MetricCard label="DSCR Stress" value={d.dscr_summary?.dscr_stress?.toFixed(3)} />
              <MetricCard label="CoC Return" value={`${((d.dscr_summary?.coc_return || 0) * 100).toFixed(2)}%`} />
              <MetricCard label="5yr IRR" value={`${((d.dscr_summary?.irr_5yr || 0) * 100).toFixed(2)}%`} />
              <MetricCard label="Lender Approval" value={`${((d.lender_summary?.approval_probability || 0) * 100).toFixed(0)}%`} variant={d.lender_summary?.approval_probability >= 0.7 ? "good" : "warn"} />
              <MetricCard label="Best Rate" value={d.lender_summary?.best_rate ? `${(d.lender_summary.best_rate * 100).toFixed(2)}%` : "N/A"} />
            </div>

            {d.reasoning?.length > 0 && (
              <div className="mb-3">
                <p className="text-green-400 text-xs font-bold mb-1">REASONING</p>
                <ul className="space-y-0.5">
                  {d.reasoning.map((r: string, i: number) => <li key={i} className="text-sm text-green-200">+ {r}</li>)}
                </ul>
              </div>
            )}

            {d.risk_flags?.length > 0 && (
              <div>
                <p className="text-yellow-400 text-xs font-bold mb-1">RISK FLAGS</p>
                <ul className="space-y-0.5">
                  {d.risk_flags.map((r: string, i: number) => <li key={i} className="text-sm text-yellow-200">! {r}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
