import { formatCurrency, formatPercent, pnlColorClass } from "../lib/format";

export default function RebalanceTable({ rows }) {
  if (!rows?.length) {
    return <EmptyState message="No rebalance periods yet." />;
  }

  return (
    <div className="max-h-[420px] overflow-auto rounded-xl border border-white/10">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-md">
          <tr className="text-left text-xs text-slate-400 uppercase tracking-wider">
            <Th>Period</Th>
            <Th>Start Date</Th>
            <Th>End Date</Th>
            <Th align="right">Starting Value</Th>
            <Th align="right">Ending Value</Th>
            <Th align="right">Net PnL ($)</Th>
            <Th align="right">Return (%)</Th>
          </tr>
        </thead>
        <tbody className="font-mono tabular-nums">
          {rows.map((row) => (
            <tr
              key={row.Period}
              className="border-t border-white/5 hover:bg-white/5 transition-colors"
            >
              <Td>{row.Period}</Td>
              <Td className="font-sans">{row["Start Date"]}</Td>
              <Td className="font-sans">{row["End Date"]}</Td>
              <Td align="right">{formatCurrency(row["Starting Value"])}</Td>
              <Td align="right">{formatCurrency(row["Ending Value"])}</Td>
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

export function Th({ children, align = "left" }) {
  return (
    <th className={`px-4 py-2.5 font-medium ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

export function Td({ children, align = "left", className = "" }) {
  return (
    <td className={`px-4 py-2 text-slate-200 ${align === "right" ? "text-right" : "text-left"} ${className}`}>
      {children}
    </td>
  );
}

export function EmptyState({ message }) {
  return (
    <div className="h-40 flex items-center justify-center text-sm text-slate-500 rounded-xl border border-white/10 border-dashed">
      {message}
    </div>
  );
}
