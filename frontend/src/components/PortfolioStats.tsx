"use client";

interface PortfolioData {
  balance: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  best_trade: number;
  worst_trade: number;
}

interface Props {
  portfolio: PortfolioData;
  currentPrice: number;
  pair: string;
}

export default function PortfolioStats({ portfolio, currentPrice, pair }: Props) {
  const pnlColor = portfolio.total_pnl >= 0 ? "text-accent-green" : "text-accent-red";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="card">
        <p className="text-xs text-gray-500 mb-1">Balance</p>
        <p className="text-xl font-bold">${portfolio.balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
      </div>

      <div className="card">
        <p className="text-xs text-gray-500 mb-1">Total PnL</p>
        <p className={`text-xl font-bold ${pnlColor}`}>
          {portfolio.total_pnl >= 0 ? "+" : ""}${portfolio.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
      </div>

      <div className="card">
        <p className="text-xs text-gray-500 mb-1">Win Rate</p>
        <p className="text-xl font-bold">
          {portfolio.win_rate}%
          <span className="text-xs text-gray-500 ml-1">
            ({portfolio.winning_trades}W / {portfolio.losing_trades}L)
          </span>
        </p>
      </div>

      <div className="card">
        <p className="text-xs text-gray-500 mb-1">{pair}</p>
        <p className="text-xl font-bold text-accent-blue">
          ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
      </div>
    </div>
  );
}
