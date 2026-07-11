import { useState } from "react";
import { Loader2, Calculator } from "lucide-react";

import { getAverageStats } from "../lib/api";
import { formatCurrency, formatPercent, pnlColorClass } from "../lib/format";

const MAX_RUNS = 100;

/**
 * Lets the user pick how many of the most recent recorded backtest runs to
 * average over (1-100) and shows avg Net PnL / Total Return % / Win Rate %.
 * Every successful POST /api/v1/backtest call on the backend is recorded to
 * a persisted history, which is what this reads from.
 */
export default function HistoryAverageTab() {
  const [numRuns, setNumRuns] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAverageStats(numRuns);
      setStats(data);
    } catch (err) {
      setStats(null);
      setError(err.message || "Something went wrong while computing the average.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-2">
          <span className="text-xs font-medium text-slate-400">
            Number of previous runs (1–{MAX_RUNS})
          </span>
          <input
            type="number"
            min={1}
            max={MAX_RUNS}
            value={numRuns}
            onChange={(e) => setNumRuns(Number(e.target.value))}
            className="w-40 rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition"
          />
        </label>

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/20"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calculator className="w-4 h-4" />}
          Calculate Average
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {stats && !error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatTile
              label="Avg Net PnL ($)"
              value={formatCurrency(stats.avg_net_pnl)}
              colorClass={pnlColorClass(stats.avg_net_pnl)}
            />
            <StatTile
              label="Avg Total Return (%)"
              value={formatPercent(stats.avg_total_return_pct)}
              colorClass={pnlColorClass(stats.avg_total_return_pct)}
            />
            <StatTile
              label="Avg Win Rate (%)"
              value={
                stats.avg_win_rate_pct === null || stats.avg_win_rate_pct === undefined
                  ? "—"
                  : `${stats.avg_win_rate_pct.toFixed(1)}%`
              }
            />
          </div>
          <p className="text-xs text-slate-500">
            Averaged over {stats.num_runs_used} run(s), from {stats.oldest_run_timestamp?.slice(0, 19).replace("T", " ")}{" "}
            to {stats.newest_run_timestamp?.slice(0, 19).replace("T", " ")}.
          </p>
        </>
      )}

      {!stats && !error && (
        <p className="text-sm text-slate-500">
          Pick how many recent runs to average and click "Calculate Average". Each backtest
          you run is automatically added to history (up to the last {MAX_RUNS}).
        </p>
      )}
    </div>
  );
}

function StatTile({ label, value, colorClass = "text-slate-100" }) {
  return (
    <div className="rounded-xl bg-black/30 border border-white/10 p-4 flex flex-col gap-2">
      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      <span className={`text-xl font-semibold font-mono tabular-nums ${colorClass}`}>{value}</span>
    </div>
  );
}
