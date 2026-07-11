import { Wallet, Layers, CalendarClock, Play, Loader2 } from "lucide-react";

/**
 * Left control panel: strategy inputs + the primary "Run Backtest" action.
 * Purely controlled -- all state lives in App.jsx.
 */
export default function Sidebar({ form, onChange, onSubmit, loading }) {
  return (
    <aside className="w-full lg:w-80 shrink-0 flex flex-col gap-6">
      <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-6 shadow-2xl shadow-black/40">
        <div className="flex items-center gap-2.5 mb-1">
          <div>
            <h1 className="text-base font-semibold text-slate-100 tracking-tight">
              Micro-Cap Quant Engine
            </h1>
            <p className="text-xs text-slate-500">Random-basket backtester</p>
          </div>
        </div>

        <div className="h-px bg-white/10 my-5" />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
          className="flex flex-col gap-5"
        >
          <Field
            icon={<Wallet className="w-3.5 h-3.5" />}
            label="Initial Capital ($)"
          >
            <input
              type="number"
              min={1}
              step={1}
              value={form.initialCapital}
              onChange={(e) => onChange("initialCapital", Number(e.target.value))}
              className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition"
            />
          </Field>

          <Field
            icon={<Layers className="w-3.5 h-3.5" />}
            label="Number of Stocks"
            trailing={
              <span className="font-mono text-sm text-blue-400 tabular-nums">
                {form.numStocks}
              </span>
            }
          >
            <input
              type="range"
              min={1}
              max={50}
              step={1}
              value={form.numStocks}
              onChange={(e) => onChange("numStocks", Number(e.target.value))}
              className="w-full accent-blue-500 cursor-pointer"
            />
          </Field>

          <Field
            icon={<CalendarClock className="w-3.5 h-3.5" />}
            label="Holding Period (weeks)"
          >
            <input
              type="number"
              min={1}
              step={1}
              value={form.holdingPeriodWeeks}
              onChange={(e) => onChange("holdingPeriodWeeks", Number(e.target.value))}
              className="w-full rounded-lg bg-black/30 border border-white/10 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition"
            />
          </Field>

          <button
            type="submit"
            disabled={loading}
            className={`mt-2 relative flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25 ${
              loading ? "" : "animate-glow"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running backtest…
              </>
            ) : (
              <>
                <Play className="w-4 h-4" fill="currentColor" />
                Run Backtest
              </>
            )}
          </button>
        </form>
      </div>

      <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-5 text-xs text-slate-500 leading-relaxed">
        Each run randomly draws a fresh basket every rebalance period from a
        ~500-name US micro-cap universe. Results are non-deterministic by
        design, re-run to sample a new random path.
      </div>
    </aside>
  );
}

function Field({ icon, label, trailing, children }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="flex items-center justify-between text-xs font-medium text-slate-400">
        <span className="flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        {trailing}
      </span>
      {children}
    </label>
  );
}
