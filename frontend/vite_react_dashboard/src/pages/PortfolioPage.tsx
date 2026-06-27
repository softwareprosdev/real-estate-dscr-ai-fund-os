import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import MetricCard from "../components/MetricCard";

export default function PortfolioPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => api.get<any>("/portfolio/summary"),
    refetchInterval: 30_000,
  });

  if (isLoading) return <p className="text-gray-400">Loading portfolio...</p>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-green-400">Portfolio Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Properties" value={data?.total_properties ?? 0} />
        <MetricCard label="Deployed Capital" value={`$${(data?.total_deployed_capital ?? 0).toLocaleString()}`} />
        <MetricCard label="Portfolio DSCR" value={(data?.portfolio_dscr ?? 0).toFixed(3)} variant={data?.portfolio_dscr >= 1.2 ? "good" : "bad"} />
        <MetricCard label="Monthly Cash Flow" value={`$${(data?.total_monthly_cash_flow ?? 0).toLocaleString()}`} variant={data?.total_monthly_cash_flow > 0 ? "good" : "bad"} />
        <MetricCard label="Portfolio NOI" value={`$${(data?.portfolio_noi ?? 0).toLocaleString()}`} />
        <MetricCard label="Avg CoC Return" value={`${((data?.avg_coc_return ?? 0) * 100).toFixed(2)}%`} />
      </div>
      <p className="text-gray-500 text-sm">Acquire properties via the Decision engine to populate your portfolio.</p>
    </div>
  );
}
