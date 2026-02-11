"use client";

import { useEffect, useState, useCallback } from "react";
import { getMarketAnalysis } from "@/lib/api";

interface Insight {
  indicator: string;
  value: string | number;
  signal: string;
  overlay: string;
  title: string;
  text: string;
  tip: string;
}

interface AnalysisData {
  price: number;
  pair: string;
  timeframe: string;
  overall: string;
  summary: string;
  insights: Insight[];
  indicators: Record<string, number>;
}

interface MarketInsightProps {
  timeframe: string;
  onToggleOverlay?: (overlay: string) => void;
}

const SIGNAL_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  bullish: { bg: "bg-green-500/10", text: "text-green-400", dot: "bg-green-400" },
  mild_bullish: { bg: "bg-green-500/5", text: "text-green-300", dot: "bg-green-300" },
  bearish: { bg: "bg-red-500/10", text: "text-red-400", dot: "bg-red-400" },
  mild_bearish: { bg: "bg-red-500/5", text: "text-red-300", dot: "bg-red-300" },
  neutral: { bg: "bg-gray-500/10", text: "text-gray-400", dot: "bg-gray-400" },
};

const OVERALL_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
  bullish: { bg: "bg-green-500/15 border-green-500/30", text: "text-green-400", icon: "▲" },
  bearish: { bg: "bg-red-500/15 border-red-500/30", text: "text-red-400", icon: "▼" },
  neutral: { bg: "bg-yellow-500/15 border-yellow-500/30", text: "text-yellow-400", icon: "◆" },
};

const OVERLAY_LABELS: Record<string, string> = {
  ema_9: "EMA 9",
  ema_21: "EMA 21",
  ema_50: "EMA 50",
  ema_200: "EMA 200",
  bb: "Bollinger",
};

export default function MarketInsight({ timeframe, onToggleOverlay }: MarketInsightProps) {
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAnalysis = useCallback(async () => {
    try {
      const data = await getMarketAnalysis({ timeframe });
      setAnalysis(data);
    } catch (err) {
      console.error("Failed to load analysis:", err);
    } finally {
      setLoading(false);
    }
  }, [timeframe]);

  useEffect(() => {
    loadAnalysis();
    const interval = setInterval(loadAnalysis, 30000);
    return () => clearInterval(interval);
  }, [loadAnalysis]);

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-bg-tertiary rounded w-1/2" />
          <div className="h-3 bg-bg-tertiary rounded w-3/4" />
          <div className="h-3 bg-bg-tertiary rounded w-2/3" />
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const overall = OVERALL_STYLES[analysis.overall] || OVERALL_STYLES.neutral;

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header — Overall Sentiment */}
      <div className={`px-4 py-3 border-b border-border ${overall.bg}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-lg ${overall.text}`}>{overall.icon}</span>
          <h3 className={`font-bold text-sm ${overall.text}`}>
            Market {analysis.overall.toUpperCase()}
          </h3>
          <span className="text-xs text-gray-500 ml-auto">{analysis.timeframe}</span>
        </div>
        <p className="text-xs text-gray-400">{analysis.summary}</p>
      </div>

      {/* Insights List */}
      <div className="divide-y divide-border">
        {analysis.insights.map((insight, i) => {
          const colors = SIGNAL_COLORS[insight.signal] || SIGNAL_COLORS.neutral;
          const isExpanded = expandedIndex === i;

          return (
            <div key={i} className="group">
              {/* Insight Header (clickable) */}
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : i)}
                className="w-full text-left px-4 py-3 hover:bg-bg-tertiary/50 transition"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${colors.dot}`} />
                  <span className={`text-xs font-semibold ${colors.text}`}>
                    {insight.indicator}
                  </span>
                  <span className="text-xs text-gray-300 flex-1 truncate">
                    {insight.title}
                  </span>
                  <span className="text-xs text-gray-600">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>
              </button>

              {/* Expanded Detail */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-3">
                  {/* Explanation */}
                  <div className={`${colors.bg} rounded-lg p-3`}>
                    <p className="text-sm text-gray-300 leading-relaxed">
                      {insight.text}
                    </p>
                  </div>

                  {/* Tip */}
                  <div className="bg-accent-yellow/10 rounded-lg p-3 border border-accent-yellow/20">
                    <p className="text-xs font-semibold text-accent-yellow mb-1">
                      Tip Belajar:
                    </p>
                    <p className="text-xs text-gray-300 leading-relaxed">
                      {insight.tip}
                    </p>
                  </div>

                  {/* Show on Chart button */}
                  {insight.overlay && onToggleOverlay && (
                    <button
                      onClick={() => onToggleOverlay(insight.overlay)}
                      className="flex items-center gap-2 text-xs text-accent-blue hover:text-accent-blue/80 transition"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      Tunjuk {OVERLAY_LABELS[insight.overlay] || insight.overlay} kat Chart
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Indicator Bar */}
      <div className="px-4 py-3 bg-bg-tertiary/50 border-t border-border">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-[10px] text-gray-500">RSI</p>
            <p className={`text-xs font-bold ${
              analysis.indicators.rsi <= 30 ? "text-green-400" :
              analysis.indicators.rsi >= 70 ? "text-red-400" : "text-gray-300"
            }`}>
              {analysis.indicators.rsi}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500">MACD</p>
            <p className={`text-xs font-bold ${
              analysis.indicators.macd_histogram > 0 ? "text-green-400" : "text-red-400"
            }`}>
              {analysis.indicators.macd_histogram > 0 ? "+" : ""}
              {analysis.indicators.macd_histogram?.toFixed(0)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500">ADX</p>
            <p className={`text-xs font-bold ${
              analysis.indicators.adx >= 25 ? "text-accent-blue" : "text-gray-500"
            }`}>
              {analysis.indicators.adx}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
