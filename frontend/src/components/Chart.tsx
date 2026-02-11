"use client";

import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";

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

interface ChartProps {
  candles: Candle[];
  markers?: TradeMarker[];
  height?: number;
}

export default function Chart({ candles, markers = [], height = 400 }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

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
        vertLines: { color: "#1c2128" },
        horzLines: { color: "#1c2128" },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: "#30363d",
      },
      timeScale: {
        borderColor: "#30363d",
        timeVisible: true,
      },
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

    // Resize handler
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [height]);

  // Update data
  useEffect(() => {
    if (!seriesRef.current || !candles.length) return;

    const chartData: CandlestickData[] = candles.map((c) => ({
      time: (new Date(c.timestamp).getTime() / 1000) as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    seriesRef.current.setData(chartData);

    // Add trade markers
    if (markers.length > 0) {
      const markerData = markers.map((m) => ({
        time: (new Date(m.time).getTime() / 1000) as Time,
        position: m.side === "BUY" ? ("belowBar" as const) : ("aboveBar" as const),
        color: m.side === "BUY" ? "#3fb950" : "#f85149",
        shape: m.side === "BUY" ? ("arrowUp" as const) : ("arrowDown" as const),
        text: m.side,
      }));
      seriesRef.current.setMarkers(markerData);
    }

    chartRef.current?.timeScale().fitContent();
  }, [candles, markers]);

  return (
    <div className="card p-0 overflow-hidden">
      <div ref={containerRef} />
    </div>
  );
}
