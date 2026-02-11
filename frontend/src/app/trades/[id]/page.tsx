"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ExplanationCard from "@/components/ExplanationCard";
import { getTradeDetail } from "@/lib/api";

interface TradeDetail {
  trade: {
    id: number;
    pair: string;
    side: string;
    entry_price: number;
    exit_price: number | null;
    quantity: number;
    stop_loss: number | null;
    take_profit: number | null;
    status: string;
    pnl: number | null;
    pnl_percent: number | null;
    strategy: string;
    timeframe: string;
    confluence_score: number;
    created_at: string;
    closed_at: string | null;
  };
  explanation: {
    full_text: string;
    reasons: string[];
    learning_points: string[];
    risk_reward_ratio: number | null;
    indicators: Record<string, number>;
  } | null;
  post_analysis: {
    result_summary: string;
    what_went_right: string[] | null;
    what_went_wrong: string[] | null;
    improvements: string[] | null;
    lesson: string;
  } | null;
  snapshot: Record<string, number> | null;
}

export default function TradeDetailPage() {
  const params = useParams();
  const [data, setData] = useState<TradeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      getTradeDetail(Number(params.id))
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center mt-20">
        <p className="text-gray-500">Trade not found</p>
        <a href="/" className="text-accent-blue hover:underline text-sm">Back to Dashboard</a>
      </div>
    );
  }

  const { trade } = data;
  const pnlColor = trade.pnl === null ? "text-gray-500" : trade.pnl >= 0 ? "text-accent-green" : "text-accent-red";

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <a href="/" className="text-gray-500 hover:text-white text-sm">&larr; Dashboard</a>
        <span className="text-gray-600">/</span>
        <span className="text-sm">Trade #{trade.id}</span>
      </div>

      {/* Trade Summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className={trade.side === "BUY" ? "badge-buy" : "badge-sell"}>
              {trade.side}
            </span>
            <span className="text-xl font-bold">{trade.pair}</span>
            <span className={trade.status === "OPEN" ? "badge-open" : "badge-closed"}>
              {trade.status}
            </span>
          </div>
          {trade.pnl !== null && (
            <div className="text-right">
              <p className={`text-2xl font-bold ${pnlColor}`}>
                {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
              </p>
              <p className={`text-sm ${pnlColor}`}>
                {(trade.pnl_percent ?? 0) >= 0 ? "+" : ""}{trade.pnl_percent?.toFixed(2)}%
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500">Entry Price</p>
            <p className="font-mono">${trade.entry_price.toLocaleString()}</p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500">Exit Price</p>
            <p className="font-mono">{trade.exit_price ? `$${trade.exit_price.toLocaleString()}` : "-"}</p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500">Stop Loss</p>
            <p className="font-mono text-accent-red">{trade.stop_loss ? `$${trade.stop_loss.toLocaleString()}` : "-"}</p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500">Take Profit</p>
            <p className="font-mono text-accent-green">{trade.take_profit ? `$${trade.take_profit.toLocaleString()}` : "-"}</p>
          </div>
        </div>

        <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
          <span>Strategy: <strong className="text-gray-300">{trade.strategy}</strong></span>
          <span>Timeframe: <strong className="text-gray-300">{trade.timeframe}</strong></span>
          <span>Confluence: <strong className="text-gray-300">{trade.confluence_score}/5</strong></span>
          <span>Opened: {new Date(trade.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Explanation */}
      <ExplanationCard explanation={data.explanation} postAnalysis={data.post_analysis} />
    </div>
  );
}
