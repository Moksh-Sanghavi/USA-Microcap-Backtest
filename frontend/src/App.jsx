import { useState } from "react";
import { Wallet, TrendingUp, Percent, Target } from "lucide-react";

import Sidebar from "./components/Sidebar";
import KpiCard from "./components/KpiCard";
import EquityChart from "./components/EquityChart";
import ResultsTabs from "./components/ResultsTabs";
import ErrorToast from "./components/ErrorToast";
import { runBacktest } from "./lib/api";
import { formatCurrency, formatPercent, pnlColorClass } from "./lib/format";

const DEFAULT_FORM = {
  initialCapital: 100,
  numStocks: 10,
  holdingPeriodWeeks: 2,
};

/** Build [{ date, value }] equity-curve points from the rebalance summary. */
function buildEquityCurve(rebalanceSummary, initialCapital) {
  if (!rebalanceSummary?.length) return [];
  const points = [{ date: rebalanceSummary[0]["Start Date"], value: initialCapital }];
  for (const period of rebalanceSummary) {
    points.push({ date: period["End Date"], value: period["Ending Value"] });
  }
  return points;
}

export default function App() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleChange = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runBacktest(form);
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong while running the backtest.");
    } finally {
      setLoading(false);
    }
  };

  const metrics = result?.global_metrics;
  const equityCurve = buildEquityCurve(result?.rebalance_summary, form.initialCapital);

  return (
    <div className="min-h-screen bg-[#05050a] relative overflow-x-hidden">
      {/* Ambient background glow -- purely decorative, matches the "finance terminal" brief */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-[1600px] mx-auto px-6 py-8 flex flex-col lg:flex-row gap-6">
        <Sidebar form={form} onChange={handleChange} onSubmit={handleSubmit} loading={loading} />

        <main className="flex-1 flex flex-col gap-6 min-w-0">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <KpiCard
              label="Final Portfolio Value"
              value={formatCurrency(metrics?.["Final Portfolio Value"])}
              icon={<Wallet className="w-4 h-4" />}
              loading={loading}
            />
            <KpiCard
              label="Net PnL ($)"
              value={formatCurrency(metrics?.["Overall Net PnL"])}
              colorClass={pnlColorClass(metrics?.["Overall Net PnL"])}
              icon={<TrendingUp className="w-4 h-4" />}
              loading={loading}
            />
            <KpiCard
              label="Total Return (%)"
              value={formatPercent(metrics?.["Total Strategy Return (%)"])}
              colorClass={pnlColorClass(metrics?.["Total Strategy Return (%)"])}
              icon={<Percent className="w-4 h-4" />}
              loading={loading}
            />
            <KpiCard
              label="Win Rate (%)"
              value={
                metrics?.["Win Rate (%)"] === null || metrics?.["Win Rate (%)"] === undefined
                  ? "—"
                  : `${metrics["Win Rate (%)"].toFixed(1)}%`
              }
              icon={<Target className="w-4 h-4" />}
              loading={loading}
            />
          </div>

          {/* Net PnL / Return above are measured against total capital CONTRIBUTED,
              not just the initial deposit -- the capital-floor rule injects fresh
              cash whenever the portfolio dips below the initial amount. Surface
              that breakdown so the KPI math is never a mystery. */}
          {metrics && !loading && metrics["Additional Capital Injected"] > 0.005 && (
            <div className="rounded-xl bg-blue-500/5 border border-blue-500/20 px-4 py-2.5 text-xs text-slate-400 flex flex-wrap gap-x-6 gap-y-1 font-mono">
              <span>Initial Capital: <span className="text-slate-200">{formatCurrency(metrics["Total Initial Capital"])}</span></span>
              <span>+ Capital Injected (floor top-ups): <span className="text-amber-400">{formatCurrency(metrics["Additional Capital Injected"])}</span></span>
              <span>= Total Capital Contributed: <span className="text-slate-200">{formatCurrency(metrics["Total Capital Contributed"])}</span></span>
              <span className="text-slate-500">(PnL and Return % are measured against this contributed total, not just the initial deposit)</span>
            </div>
          )}

          <EquityChart data={equityCurve} loading={loading} />

          <ResultsTabs
            rebalanceSummary={result?.rebalance_summary}
            tradeLedger={result?.trade_ledger}
            loading={loading}
          />
        </main>
      </div>

      <ErrorToast message={error} onDismiss={() => setError(null)} />
    </div>
  );
}
