import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { formatCurrency } from "../lib/format";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  return (
    <div className="rounded-lg bg-slate-950/95 backdrop-blur-md border border-white/10 px-3 py-2 shadow-2xl">
      <p className="text-[11px] text-slate-400 mb-1">{label}</p>
      <p className="text-sm font-mono font-semibold text-blue-400">
        {formatCurrency(value)}
      </p>
    </div>
  );
}

/**
 * data: [{ date: "2025-07-11", value: 100.0 }, ...]
 */
export default function EquityChart({ data, loading }) {
  return (
    <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-6 shadow-xl shadow-black/30">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-200">Equity Curve</h2>
        <span className="text-xs text-slate-500">Portfolio value over time</span>
      </div>

      <div className="h-80">
        {loading ? (
          <div className="w-full h-full rounded-xl bg-white/5 animate-pulse" />
        ) : !data?.length ? (
          <div className="w-full h-full flex items-center justify-center text-sm text-slate-500">
            Run a backtest to see the equity curve.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                tickLine={false}
                minTickGap={40}
              />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}
                axisLine={false}
                tickLine={false}
                width={64}
                tickFormatter={(v) => `$${v.toFixed(0)}`}
                domain={["auto", "auto"]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#equityFill)"
                dot={false}
                activeDot={{ r: 4, fill: "#3b82f6", stroke: "#0a0a0a", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
