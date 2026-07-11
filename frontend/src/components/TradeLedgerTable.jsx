import { formatCurrency, formatPercent, pnlColorClass } from "../lib/format";
import { Th, Td, EmptyState } from "./RebalanceTable";

export default function TradeLedgerTable({ rows }) {
  if (!rows?.length) {
    return <EmptyState message="No trades yet." />;
  }

  return (
    <div className="max-h-[420px] overflow-auto rounded-xl border border-white/10">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-md">
          <tr className="text-left text-xs text-slate-400 uppercase tracking-wider">
            <Th>Period</Th>
            <Th>Ticker</Th>
            <Th align="right">Entry Price</Th>
            <Th align="right">Exit Price</Th>
            <Th align="right">Invested ($)</Th>
            <Th align="right">Net PnL ($)</Th>
            <Th align="right">Return (%)</Th>
          </tr>
        </thead>
        <tbody className="font-mono tabular-nums">
          {rows.map((row, i) => (
            <tr
              key={`${row.Period}-${row.Ticker}-${i}`}
              className="border-t border-white/5 hover:bg-white/5 transition-colors"
            >
              <Td>{row.Period}</Td>
              <Td className="font-sans font-semibold text-slate-100">{row.Ticker}</Td>
              <Td align="right">{formatCurrency(row["Entry Price"], { decimals: 2 })}</Td>
              <Td align="right">{formatCurrency(row["Exit Price"], { decimals: 2 })}</Td>
              <Td align="right">{formatCurrency(row["Invested Capital ($)"])}</Td>
              <Td align="right" className={pnlColorClass(row["Net PnL ($)"])}>
                {formatCurrency(row["Net PnL ($)"])}
              </Td>
              <Td align="right" className={pnlColorClass(row["Return (%)"])}>
                {formatPercent(row["Return (%)"])}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
