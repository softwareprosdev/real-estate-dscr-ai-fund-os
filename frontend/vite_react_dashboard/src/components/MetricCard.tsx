import clsx from "clsx";

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  variant?: "default" | "good" | "warn" | "bad";
}

export default function MetricCard({ label, value, sub, variant = "default" }: MetricCardProps) {
  const colors = {
    default: "border-gray-700",
    good: "border-green-500",
    warn: "border-yellow-500",
    bad: "border-red-500",
  };

  return (
    <div className={clsx("bg-gray-900 rounded-lg border p-4", colors[variant])}>
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}
