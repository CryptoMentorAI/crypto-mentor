"use client";

import { useEffect, useState } from "react";
import Chart from "@/components/Chart";
import PortfolioStats from "@/components/PortfolioStats";
import TradeLog from "@/components/TradeLog";
import ExplanationCard from "@/components/ExplanationCard";
import { getDashboard, getCandles, getTradeDetail } from "@/lib/api";
import wsClient from "@/lib/websocket";

interface DashboardData {
  portfolio: {
    balance: number;
    total_pnl: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    best_trade: number;
    worst_trade: number;
  };
  current_price: number;
  pair: string;
  open_trades: Trade[];
  recent_trades: Trade[];
}

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

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [overlays, setOverlays] = useState<Record<string, unknown> | null>(null);
  const [srLevels, setSrLevels] = useState<{ price: number; type: "support" | "resistance"; strength: number; touches: number }[]>([]);
  const [selectedExplanation, setSelectedExplanation] = useState<{
    explanation: unknown;
    postAnalysis: unknown;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    wsClient.connect();

    wsClient.on("price_update", () => {
      // Refresh dashboard on price update
      loadData();
    });

    wsClient.on("new_trade", () => {
      loadData();
    });

    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);

    return () => {
      clearInterval(interval);
      wsClient.disconnect();
    };
  }, []);

  async function loadData() {
    try {
      const [dashData, candleData] = await Promise.all([
        getDashboard(),
        getCandles({ limit: 100 }),
      ]);
      setDashboard(dashData);
      setCandles(candleData.candles);
      setOverlays(candleData.overlays || null);
      setSrLevels(candleData.sr_levels || []);
      setError(null);
    } catch (err) {
      setError("Tak dapat connect ke backend. Pastikan server dah start.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleTradeClick(tradeId: number) {
    try {
      const detail = await getTradeDetail(tradeId);
      setSelectedExplanation({
        explanation: detail.explanation,
        postAnalysis: detail.post_analysis,
      });
    } catch (err) {
      console.error("Failed to load trade detail:", err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-gray-500">Loading CryptoMentor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto mt-20">
        <div className="card text-center">
          <p className="text-accent-red text-lg mb-2">Connection Error</p>
          <p className="text-gray-400 text-sm mb-4">{error}</p>
          <div className="bg-bg-tertiary rounded p-4 text-left text-xs font-mono">
            <p className="text-gray-500 mb-2"># Start backend:</p>
            <p className="text-accent-green">cd Desktop/crypto-mentor/backend</p>
            <p className="text-accent-green">pip install -r requirements.txt</p>
            <p className="text-accent-green">uvicorn backend.main:app --reload</p>
          </div>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-accent-blue/20 text-accent-blue rounded hover:bg-accent-blue/30 transition text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  const tradeMarkers = [...dashboard.open_trades, ...dashboard.recent_trades]
    .filter((t) => t.created_at)
    .map((t) => ({
      time: t.created_at,
      side: t.side as "BUY" | "SELL",
      price: t.entry_price,
    }));

  return (
    <div className="space-y-4">
      {/* Portfolio Stats */}
      <PortfolioStats
        portfolio={dashboard.portfolio}
        currentPrice={dashboard.current_price}
        pair={dashboard.pair}
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chart + Trade Log (2/3) */}
        <div className="lg:col-span-2 space-y-4">
          <Chart
            candles={candles}
            markers={tradeMarkers}
            overlays={overlays as Parameters<typeof Chart>[0]["overlays"]}
            srLevels={srLevels}
            height={500}
          />

          {/* Open Trades */}
          {dashboard.open_trades.length > 0 && (
            <TradeLog
              trades={dashboard.open_trades}
              title="Open Positions"
              onTradeClick={handleTradeClick}
            />
          )}

          {/* Recent Trades */}
          <TradeLog
            trades={dashboard.recent_trades}
            title="Recent Trades"
            onTradeClick={handleTradeClick}
          />
        </div>

        {/* Explanation Panel (1/3) */}
        <div className="space-y-4">
          <ExplanationCard
            explanation={selectedExplanation?.explanation as Parameters<typeof ExplanationCard>[0]["explanation"]}
            postAnalysis={selectedExplanation?.postAnalysis as Parameters<typeof ExplanationCard>[0]["postAnalysis"]}
          />

          {/* Quick Tips */}
          <div className="card">
            <h3 className="font-semibold mb-3 text-accent-yellow">Tips</h3>
            <div className="space-y-2 text-sm text-gray-400">
              <p>Klik mana-mana trade untuk tengok explanation kenapa bot buat keputusan tu.</p>
              <p>Bot scan market setiap minit dan cari confluence dari 4 strategy berbeza.</p>
              <p>Pergi ke <a href="/learn" className="text-accent-blue hover:underline">Belajar</a> untuk faham setiap indicator.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
