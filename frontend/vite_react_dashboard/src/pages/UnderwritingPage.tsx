import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import MetricCard from "../components/MetricCard";

const DEFAULTS = {
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
};

export default function UnderwritingPage() {
  const [form, setForm] = useState(DEFAULTS);

  const mutation = useMutation({
    mutationFn: (data: typeof DEFAULTS) => api.post<any>("/underwriting/analyze", data),
  });

  const r = mutation.data?.dscr_result;
  const dscrVariant = (dscr?: number) =>
    !dscr ? "default" : dscr >= 1.25 ? "good" : dscr >= 1.20 ? "warn" : "bad";

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-green-400">DSCR Underwriting Engine</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(DEFAULTS).map(([key, val]) => (
          <label key={key} className="flex flex-col gap-1">
            <span className="text-xs text-gray-400 uppercase">{key.replace(/_/g, " ")}</span>
            <input
              type="number"
              step="any"
              className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
              value={(form as any)[key]}
              onChange={(e) => setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))}
            />
          </label>
        ))}
      </div>

      <button
        onClick={() => mutation.mutate(form)}
        disabled={mutation.isPending}
        className="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded font-bold disabled:opacity-50"
      >
        {mutation.isPending ? "Analyzing..." : "Run Underwriting"}
      </button>

      {mutation.error && (
        <p className="text-red-400 text-sm">{String(mutation.error)}</p>
      )}

      {r && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-black ${mutation.data.recommendation === "STRONG_BUY" || mutation.data.recommendation === "BUY" ? "text-green-400" : mutation.data.recommendation === "CONDITIONAL" ? "text-yellow-400" : "text-red-400"}`}>
              {mutation.data.recommendation}
            </span>
            <span className="text-gray-400 text-sm">Confidence: {(mutation.data.underwriting_confidence * 100).toFixed(0)}%</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="DSCR Base" value={r.dscr_base.toFixed(3)} variant={dscrVariant(r.dscr_base)} />
            <MetricCard label="DSCR Stress" value={r.dscr_combined_stress.toFixed(3)} variant={dscrVariant(r.dscr_combined_stress)} />
            <MetricCard label="NOI" value={`$${r.noi.toLocaleString()}`} />
            <MetricCard label="Monthly CF" value={`$${r.cash_flow_monthly.toLocaleString()}`} variant={r.cash_flow_monthly > 0 ? "good" : "bad"} />
            <MetricCard label="Cap Rate" value={`${(r.cap_rate * 100).toFixed(2)}%`} />
            <MetricCard label="CoC Return" value={`${(r.cash_on_cash_return * 100).toFixed(2)}%`} variant={r.cash_on_cash_return >= 0.07 ? "good" : r.cash_on_cash_return >= 0.04 ? "warn" : "bad"} />
            <MetricCard label="5yr IRR" value={`${(r.irr_5yr_estimate * 100).toFixed(2)}%`} />
            <MetricCard label="Risk-Adj Return" value={`${(r.risk_adjusted_return * 100).toFixed(2)}%`} />
          </div>

          {mutation.data.risk_flags?.length > 0 && (
            <div className="bg-yellow-950 border border-yellow-700 rounded p-4">
              <p className="text-yellow-400 font-bold mb-2">Risk Flags</p>
              <ul className="space-y-1">
                {mutation.data.risk_flags.map((f: any) => (
                  <li key={f.flag_type} className="text-sm text-yellow-200">
                    [{f.severity.toUpperCase()}] {f.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
