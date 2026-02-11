"use client";

interface Trade {
  id: number;
  pair: string;
  side: string;
  entry_price: number;
  exit_price: number | null;
  status: string;
  pnl: number | null;
  pnl_percent: number | null;
  strategy: string;
  confluence_score: number;
  created_at: string;
}

interface Props {
  trades: Trade[];
  title?: string;
  onTradeClick?: (id: number) => void;
}

export default function TradeLog({ trades, title = "Recent Trades", onTradeClick }: Props) {
  if (!trades.length) {
    return (
      <div className="card">
        <h3 className="font-semibold mb-3">{title}</h3>
        <p className="text-gray-500 text-sm text-center py-8">
          Belum ada trades. Bot sedang scan market...
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="font-semibold mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs border-b border-border">
              <th className="text-left py-2 pr-3">Pair</th>
              <th className="text-left py-2 pr-3">Side</th>
              <th className="text-right py-2 pr-3">Entry</th>
              <th className="text-right py-2 pr-3">Exit</th>
              <th className="text-right py-2 pr-3">PnL</th>
              <th className="text-left py-2 pr-3">Strategy</th>
              <th className="text-center py-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr
                key={trade.id}
                className="border-b border-border/50 hover:bg-bg-tertiary cursor-pointer transition"
                onClick={() => onTradeClick?.(trade.id)}
              >
                <td className="py-2 pr-3 font-medium">{trade.pair}</td>
                <td className="py-2 pr-3">
                  <span className={trade.side === "BUY" ? "badge-buy" : "badge-sell"}>
                    {trade.side}
                  </span>
                </td>
                <td className="py-2 pr-3 text-right font-mono text-xs">
                  ${trade.entry_price.toLocaleString()}
                </td>
                <td className="py-2 pr-3 text-right font-mono text-xs">
                  {trade.exit_price ? `$${trade.exit_price.toLocaleString()}` : "-"}
                </td>
                <td className={`py-2 pr-3 text-right font-mono text-xs ${
                  trade.pnl === null ? "text-gray-500" :
                  trade.pnl >= 0 ? "text-accent-green" : "text-accent-red"
                }`}>
                  {trade.pnl !== null ? (
                    <>
                      {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                      <span className="text-gray-500 ml-1">
                        ({trade.pnl_percent?.toFixed(1)}%)
                      </span>
                    </>
                  ) : (
                    <span className="badge-open">OPEN</span>
                  )}
                </td>
                <td className="py-2 pr-3 text-xs text-gray-400">{trade.strategy}</td>
                <td className="py-2 text-center">
                  <ConfidenceBadge score={trade.confluence_score} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const colors = [
    "", // 0
    "bg-red-500/20 text-red-400",
    "bg-yellow-500/20 text-yellow-400",
    "bg-blue-500/20 text-blue-400",
    "bg-green-500/20 text-green-400",
    "bg-purple-500/20 text-purple-400",
  ];

  return (
    <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${colors[score] || colors[1]}`}>
      {score}/5
    </span>
  );
}
