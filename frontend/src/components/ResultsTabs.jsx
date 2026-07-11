import { useState } from "react";
import RebalanceTable from "./RebalanceTable";
import TradeLedgerTable from "./TradeLedgerTable";
import HistoryAverageTab from "./HistoryAverageTab";

const TABS = [
  { id: "rebalance", label: "Rebalance Summary" },
  { id: "ledger", label: "Detailed Trade Ledger" },
  { id: "history", label: "Historical Averages" },
];

export default function ResultsTabs({ rebalanceSummary, tradeLedger, loading }) {
  const [active, setActive] = useState("rebalance");

  return (
    <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-6 shadow-xl shadow-black/30">
      <div className="flex items-center gap-1 mb-4 p-1 rounded-xl bg-black/30 border border-white/10 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              active === tab.id
                ? "bg-gradient-to-r from-blue-600 to-violet-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {active === "history" ? (
        // Independent of the main backtest's loading state -- it has its own.
        <HistoryAverageTab />
      ) : loading ? (
        <div className="h-40 rounded-xl bg-white/5 animate-pulse" />
      ) : active === "rebalance" ? (
        <RebalanceTable rows={rebalanceSummary} />
      ) : (
        <TradeLedgerTable rows={tradeLedger} />
      )}
    </div>
  );
}
