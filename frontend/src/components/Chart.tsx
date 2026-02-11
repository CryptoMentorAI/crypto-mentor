"use client";

import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  IPriceLine,
  CandlestickData,
  LineData,
  Time,
  LineStyle,
} from "lightweight-charts";

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradeMarker {
  time: string;
  side: "BUY" | "SELL";
  price: number;
}

interface SRLevel {
  price: number;
  type: "support" | "resistance";
  strength: number;
  touches: number;
}

interface Overlays {
  ema_9: (number | null)[];
  ema_21: (number | null)[];
  ema_50: (number | null)[];
  ema_200: (number | null)[];
  bb_upper: (number | null)[];
  bb_middle: (number | null)[];
  bb_lower: (number | null)[];
  timestamps: string[];
}

interface TickUpdate {
  price: number;
  timestamp: string;
}

interface ChartProps {
  candles: Candle[];
  markers?: TradeMarker[];
  overlays?: Overlays;
  srLevels?: SRLevel[];
  height?: number;
  latestTick?: TickUpdate | null;
}

const OVERLAY_CONFIGS = {
  ema_9: { label: "EMA 9", color: "#58a6ff", default: true },
  ema_21: { label: "EMA 21", color: "#d29922", default: true },
  ema_50: { label: "EMA 50", color: "#bc8cff", default: false },
  ema_200: { label: "EMA 200", color: "#f85149", default: false },
  bb: { label: "Bollinger", color: "#8b949e", default: true },
  support: { label: "Support", color: "#00c853", default: true },
  resistance: { label: "Resistance", color: "#ff1744", default: true },
};

type OverlayKey = keyof typeof OVERLAY_CONFIGS;

export interface ChartHandle {
  toggleOverlay: (key: string) => void;
  ensureOverlay: (key: string) => void;
}

const Chart = forwardRef<ChartHandle, ChartProps>(function Chart({
  candles,
  markers = [],
  overlays,
  srLevels = [],
  height = 500,
  latestTick,
}, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lineSeriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const priceLinesRef = useRef<IPriceLine[]>([]);
  const lastCandleRef = useRef<{ time: Time; open: number; high: number; low: number; close: number } | null>(null);

  const [activeOverlays, setActiveOverlays] = useState<Set<OverlayKey>>(() => {
    const defaults = new Set<OverlayKey>();
    for (const [key, config] of Object.entries(OVERLAY_CONFIGS)) {
      if (config.default) defaults.add(key as OverlayKey);
    }
    return defaults;
  });

  const toggleOverlay = useCallback((key: OverlayKey) => {
    setActiveOverlays((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  // Ensure overlay is ON (don't toggle off if already on)
  const ensureOverlay = useCallback((key: OverlayKey) => {
    setActiveOverlays((prev) => {
      if (prev.has(key)) return prev;
      const next = new Set(prev);
      next.add(key);
      return next;
    });
  }, []);

  useImperativeHandle(ref, () => ({
    toggleOverlay: (key: string) => toggleOverlay(key as OverlayKey),
    ensureOverlay: (key: string) => ensureOverlay(key as OverlayKey),
  }), [toggleOverlay, ensureOverlay]);

  // Create chart once
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: "#0d1117" },
        textColor: "#8b949e",
      },
      grid: {
        vertLines: { color: "#161b22" },
        horzLines: { color: "#161b22" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#30363d" },
      timeScale: { borderColor: "#30363d", timeVisible: true },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#3fb950",
      downColor: "#f85149",
      borderUpColor: "#3fb950",
      borderDownColor: "#f85149",
      wickUpColor: "#3fb950",
      wickDownColor: "#f85149",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      lineSeriesRefs.current.clear();
    };
  }, [height]);

  // Update candle data + overlays
  useEffect(() => {
    const chart = chartRef.current;
    const candleSeries = seriesRef.current;
    if (!chart || !candleSeries || !candles.length) return;

    // Set candle data
    const chartData: CandlestickData[] = candles.map((c) => ({
      time: (new Date(c.timestamp).getTime() / 1000) as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeries.setData(chartData);

    // Track the last candle for live tick updates
    if (chartData.length > 0) {
      const last = chartData[chartData.length - 1];
      lastCandleRef.current = { ...last };
    }

    // Trade markers
    if (markers.length > 0) {
      const markerData = markers
        .map((m) => ({
          time: (new Date(m.time).getTime() / 1000) as Time,
          position: m.side === "BUY" ? ("belowBar" as const) : ("aboveBar" as const),
          color: m.side === "BUY" ? "#3fb950" : "#f85149",
          shape: m.side === "BUY" ? ("arrowUp" as const) : ("arrowDown" as const),
          text: m.side,
        }))
        .sort((a, b) => (a.time as number) - (b.time as number));
      candleSeries.setMarkers(markerData);
    }

    // Remove old line series
    for (const [key, series] of lineSeriesRefs.current) {
      try {
        chart.removeSeries(series);
      } catch {
        // ignore
      }
    }
    lineSeriesRefs.current.clear();

    if (!overlays || !overlays.timestamps.length) {
      chart.timeScale().fitContent();
      return;
    }

    const timestamps = overlays.timestamps.map(
      (t) => (new Date(t).getTime() / 1000) as Time
    );

    // Helper: add a line series
    const addLine = (
      key: string,
      values: (number | null)[],
      color: string,
      lineWidth: number = 1,
      lineStyle: LineStyle = LineStyle.Solid
    ) => {
      const data: LineData[] = [];
      for (let i = 0; i < timestamps.length; i++) {
        if (values[i] !== null && values[i] !== undefined) {
          data.push({ time: timestamps[i], value: values[i]! });
        }
      }
      if (data.length === 0) return;

      const series = chart.addLineSeries({
        color,
        lineWidth,
        lineStyle,
        crosshairMarkerVisible: false,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      series.setData(data);
      lineSeriesRefs.current.set(key, series);
    };

    // ─── EMA Lines ─────────────────────────
    if (activeOverlays.has("ema_9")) {
      addLine("ema_9", overlays.ema_9, "#58a6ff", 1);
    }
    if (activeOverlays.has("ema_21")) {
      addLine("ema_21", overlays.ema_21, "#d29922", 1);
    }
    if (activeOverlays.has("ema_50")) {
      addLine("ema_50", overlays.ema_50, "#bc8cff", 2);
    }
    if (activeOverlays.has("ema_200")) {
      addLine("ema_200", overlays.ema_200, "#f85149", 2, LineStyle.Dashed);
    }

    // ─── Bollinger Bands ───────────────────
    if (activeOverlays.has("bb")) {
      addLine("bb_upper", overlays.bb_upper, "rgba(139,148,158,0.5)", 1, LineStyle.Dotted);
      addLine("bb_middle", overlays.bb_middle, "rgba(139,148,158,0.3)", 1, LineStyle.Dashed);
      addLine("bb_lower", overlays.bb_lower, "rgba(139,148,158,0.5)", 1, LineStyle.Dotted);
    }

    // ─── Clear old price lines ──────────
    for (const pl of priceLinesRef.current) {
      try {
        candleSeries.removePriceLine(pl);
      } catch {
        // ignore
      }
    }
    priceLinesRef.current = [];

    // ─── Support Lines (green) ──────────
    if (activeOverlays.has("support") && srLevels.length > 0) {
      for (const level of srLevels.filter((l) => l.type === "support")) {
        const pl = candleSeries.createPriceLine({
          price: level.price,
          color: "#00c853",
          lineWidth: level.strength >= 3 ? 2 : 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `S $${level.price.toLocaleString()} (${level.touches}x)`,
        });
        priceLinesRef.current.push(pl);
      }
    }

    // ─── Resistance Lines (red) ──────────
    if (activeOverlays.has("resistance") && srLevels.length > 0) {
      for (const level of srLevels.filter((l) => l.type === "resistance")) {
        const pl = candleSeries.createPriceLine({
          price: level.price,
          color: "#ff1744",
          lineWidth: level.strength >= 3 ? 2 : 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `R $${level.price.toLocaleString()} (${level.touches}x)`,
        });
        priceLinesRef.current.push(pl);
      }
    }

    chart.timeScale().fitContent();
  }, [candles, markers, overlays, srLevels, activeOverlays]);

  // ─── Live tick update (real-time candle movement) ────
  useEffect(() => {
    if (!latestTick || !seriesRef.current || !lastCandleRef.current) return;

    const lc = lastCandleRef.current;
    const updated = {
      time: lc.time,
      open: lc.open,
      high: Math.max(lc.high, latestTick.price),
      low: Math.min(lc.low, latestTick.price),
      close: latestTick.price,
    };

    seriesRef.current.update(updated);
    lastCandleRef.current = updated;
  }, [latestTick]);

  return (
    <div className="card p-0 overflow-hidden">
      {/* Overlay Toggle Bar */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-border bg-bg-tertiary flex-wrap">
        <span className="text-xs text-gray-500 mr-2">Indicators:</span>
        {Object.entries(OVERLAY_CONFIGS).map(([key, config]) => (
          <button
            key={key}
            onClick={() => toggleOverlay(key as OverlayKey)}
            className={`px-2 py-0.5 rounded text-xs font-medium transition ${
              activeOverlays.has(key as OverlayKey)
                ? "text-white"
                : "text-gray-600 hover:text-gray-400"
            }`}
            style={{
              backgroundColor: activeOverlays.has(key as OverlayKey)
                ? `${config.color}30`
                : "transparent",
              borderColor: activeOverlays.has(key as OverlayKey)
                ? `${config.color}60`
                : "transparent",
              borderWidth: 1,
              borderStyle: "solid",
            }}
          >
            <span
              className="inline-block w-2 h-2 rounded-full mr-1"
              style={{ backgroundColor: config.color }}
            />
            {config.label}
          </button>
        ))}
      </div>

      <div ref={containerRef} />
    </div>
  );
});

export default Chart;
