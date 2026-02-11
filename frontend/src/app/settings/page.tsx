"use client";

import { useEffect, useState } from "react";
import { getSettings, getStrategies, updateStrategy } from "@/lib/api";

interface Strategy {
  id: number;
  name: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
  description: string;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, unknown> | null>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getSettings(), getStrategies()])
      .then(([settingsData, stratData]) => {
        setSettings(settingsData);
        setStrategies(stratData.strategies);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function toggleStrategy(id: number, enabled: boolean) {
    try {
      await updateStrategy(id, { enabled });
      setStrategies((prev) =>
        prev.map((s) => (s.id === id ? { ...s, enabled } : s))
      );
    } catch (err) {
      console.error("Failed to update strategy:", err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>

      {/* Bot Settings */}
      <div className="card">
        <h3 className="font-semibold mb-4">Bot Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500 mb-1">Trading Pair</p>
            <p className="font-mono">{String(settings?.pair ?? "")}</p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500 mb-1">Timeframe</p>
            <p className="font-mono">{String(settings?.timeframe ?? "")}</p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500 mb-1">Mode</p>
            <p className="font-mono">
              {settings?.mock_mode ? (
                <span className="text-accent-yellow">Mock Data</span>
              ) : (
                <span className="text-accent-green">Bybit Testnet</span>
              )}
            </p>
          </div>
          <div className="bg-bg-tertiary rounded p-3">
            <p className="text-xs text-gray-500 mb-1">Bybit API</p>
            <p className="font-mono">
              {settings?.bybit_configured ? (
                <span className="text-accent-green">Connected</span>
              ) : (
                <span className="text-gray-500">Not configured</span>
              )}
            </p>
          </div>
        </div>

        {!settings?.bybit_configured && (
          <div className="bg-accent-yellow/10 border border-accent-yellow/20 rounded p-3 mt-4">
            <p className="text-sm text-accent-yellow font-medium mb-1">
              Nak guna real Bybit Testnet data?
            </p>
            <p className="text-xs text-gray-400 mb-2">
              1. Register di{" "}
              <a
                href="https://testnet.bybit.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-blue hover:underline"
              >
                testnet.bybit.com
              </a>
            </p>
            <p className="text-xs text-gray-400 mb-2">
              2. Create API key (spot trading)
            </p>
            <p className="text-xs text-gray-400">
              3. Update <code className="bg-bg-tertiary px-1 rounded">backend/.env</code> dengan
              API key & secret, set <code className="bg-bg-tertiary px-1 rounded">MOCK_MODE=false</code>
            </p>
          </div>
        )}
      </div>

      {/* Strategy Toggle */}
      <div className="card">
        <h3 className="font-semibold mb-4">Strategies</h3>
        <p className="text-sm text-gray-500 mb-4">
          Enable/disable strategy yang bot guna. Recommended: biarkan semua ON untuk maximum confluence.
        </p>

        <div className="space-y-3">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              className="flex items-center justify-between bg-bg-tertiary rounded p-3"
            >
              <div>
                <p className="font-medium text-sm">
                  {strategy.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </p>
                <p className="text-xs text-gray-500">{strategy.description}</p>
              </div>
              <button
                onClick={() => toggleStrategy(strategy.id, !strategy.enabled)}
                className={`relative w-11 h-6 rounded-full transition ${
                  strategy.enabled ? "bg-accent-green" : "bg-gray-600"
                }`}
              >
                <span
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition ${
                    strategy.enabled ? "left-5" : "left-0.5"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* How to Start Guide */}
      <div className="card">
        <h3 className="font-semibold mb-4">Cara Start Bot</h3>
        <div className="bg-bg-tertiary rounded p-4 font-mono text-xs space-y-1">
          <p className="text-gray-500"># 1. Install Python dependencies</p>
          <p className="text-accent-green">cd Desktop/crypto-mentor/backend</p>
          <p className="text-accent-green">python -m venv venv</p>
          <p className="text-accent-green">venv\Scripts\activate</p>
          <p className="text-accent-green">pip install -r requirements.txt</p>
          <br />
          <p className="text-gray-500"># 2. Start backend</p>
          <p className="text-accent-green">
            python -m uvicorn backend.main:app --reload
          </p>
          <br />
          <p className="text-gray-500"># 3. Install frontend dependencies (new terminal)</p>
          <p className="text-accent-green">cd Desktop/crypto-mentor/frontend</p>
          <p className="text-accent-green">npm install</p>
          <p className="text-accent-green">npm run dev</p>
          <br />
          <p className="text-gray-500"># 4. Open browser</p>
          <p className="text-accent-blue">http://localhost:3000</p>
        </div>
      </div>
    </div>
  );
}
