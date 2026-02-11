import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { "Content-Type": "application/json" },
});

// ─── Dashboard ─────────────────────────────
export const getDashboard = () => api.get("/dashboard").then((r) => r.data);

// ─── Trades ────────────────────────────────
export const getTrades = (params?: {
  status?: string;
  strategy?: string;
  limit?: number;
}) => api.get("/trades", { params }).then((r) => r.data);

export const getTradeDetail = (id: number) =>
  api.get(`/trades/${id}`).then((r) => r.data);

// ─── Market ────────────────────────────────
export const getCandles = (params?: {
  pair?: string;
  timeframe?: string;
  limit?: number;
}) => api.get("/market/candles", { params }).then((r) => r.data);

export const getIndicators = () =>
  api.get("/market/indicators").then((r) => r.data);

export const getMarketAnalysis = (params?: { timeframe?: string }) =>
  api.get("/market/analysis", { params }).then((r) => r.data);

// ─── Strategies ────────────────────────────
export const getStrategies = () =>
  api.get("/strategies").then((r) => r.data);

export const updateStrategy = (id: number, data: Record<string, unknown>) =>
  api.put(`/strategies/${id}`, data).then((r) => r.data);

// ─── Learning ──────────────────────────────
export const getConcepts = () =>
  api.get("/learn/concepts").then((r) => r.data);

export const getConcept = (name: string) =>
  api.get(`/learn/concepts/${name}`).then((r) => r.data);

// ─── Analytics ─────────────────────────────
export const getAnalytics = () =>
  api.get("/analytics").then((r) => r.data);

// ─── Settings ──────────────────────────────
export const getSettings = () =>
  api.get("/settings").then((r) => r.data);

export default api;
