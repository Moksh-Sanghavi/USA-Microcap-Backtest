/**
 * Single glassmorphism KPI tile. `colorClass` drives the value's accent
 * color (emerald/rose for PnL-style metrics, neutral otherwise).
 */
export default function KpiCard({ label, value, icon, colorClass = "text-slate-100", loading }) {
  return (
    <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-5 shadow-xl shadow-black/30 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {label}
        </span>
        <span className="text-slate-500">{icon}</span>
      </div>

      {loading ? (
        <div className="h-8 w-3/4 rounded-md bg-white/10 animate-pulse" />
      ) : (
        <span className={`text-2xl font-semibold font-mono tabular-nums ${colorClass}`}>
          {value}
        </span>
      )}
    </div>
  );
}
