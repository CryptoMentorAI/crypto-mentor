"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Chart, { ChartHandle } from "@/components/Chart";
import PortfolioStats from "@/components/PortfolioStats";
import TradeLog from "@/components/TradeLog";
import ExplanationCard from "@/components/ExplanationCard";
import MarketInsight from "@/components/MarketInsight";
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

const TIMEFRAMES = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "1D" },
];

export default function Dashboard() {
  const chartComponentRef = useRef<ChartHandle>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [overlays, setOverlays] = useState<Record<string, unknown> | null>(null);
  const [srLevels, setSrLevels] = useState<{ price: number; type: "support" | "resistance"; strength: number; touches: number }[]>([]);
  const [selectedExplanation, setSelectedExplanation] = useState<{
    explanation: unknown;
    postAnalysis: unknown;
  } | null>(null);
  const [timeframe, setTimeframe] = useState("15m");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    wsClient.connect();

    wsClient.on("price_update", () => {
      loadData();
    });

    wsClient.on("new_trade", () => {
      loadData();
    });

    const interval = setInterval(loadData, 30000);

    return () => {
      clearInterval(interval);
      wsClient.disconnect();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeframe]);

  async function loadData() {
    try {
      const [dashData, candleData] = await Promise.all([
        getDashboard(),
        getCandles({ timeframe, limit: 500 }),
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

  const handleShowOverlay = useCallback((overlay: string) => {
    if (chartComponentRef.current) {
      chartComponentRef.current.ensureOverlay(overlay);
      // Scroll chart into view
      document.querySelector("[data-chart]")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, []);

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
          {/* Timeframe Selector */}
          <div className="flex items-center gap-1 bg-bg-secondary rounded-lg p-1 w-fit">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setTimeframe(tf.value)}
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  timeframe === tf.value
                    ? "bg-accent-blue text-white"
                    : "text-gray-400 hover:text-white hover:bg-bg-tertiary"
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <div data-chart>
            <Chart
              ref={chartComponentRef}
              candles={candles}
              markers={tradeMarkers}
              overlays={overlays as Parameters<typeof Chart>[0]["overlays"]}
              srLevels={srLevels}
              height={500}
            />
          </div>

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

        {/* Right Panel (1/3) */}
        <div className="space-y-4">
          {/* Market Insight — live analysis linked to chart */}
          <MarketInsight
            timeframe={timeframe}
            onToggleOverlay={handleShowOverlay}
          />

          {/* Trade Explanation */}
          <ExplanationCard
            explanation={selectedExplanation?.explanation as Parameters<typeof ExplanationCard>[0]["explanation"]}
            postAnalysis={selectedExplanation?.postAnalysis as Parameters<typeof ExplanationCard>[0]["postAnalysis"]}
          />

          {/* Quick Tips */}
          <div className="card">
            <h3 className="font-semibold mb-3 text-accent-yellow">Tips</h3>
            <div className="space-y-2 text-sm text-gray-400">
              <p>Klik insight di atas untuk belajar, tekan &quot;Tunjuk kat Chart&quot; untuk highlight indicator.</p>
              <p>Bot scan market setiap minit dan cari confluence dari 4 strategy berbeza.</p>
              <p>Pergi ke <a href="/learn" className="text-accent-blue hover:underline">Belajar</a> untuk faham lagi detail setiap indicator.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
