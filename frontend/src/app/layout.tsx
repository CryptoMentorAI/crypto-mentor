import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CryptoMentor — Belajar Trading Crypto",
  description: "Educational paper trading bot yang explain setiap keputusan",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ms">
      <body>
        <div className="min-h-screen">
          <nav className="border-b border-border bg-bg-secondary px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold">CryptoMentor</h1>
              <span className="text-xs text-gray-500 bg-bg-tertiary px-2 py-0.5 rounded">
                Paper Trading
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <a href="/" className="text-gray-400 hover:text-white transition">
                Dashboard
              </a>
              <a href="/trades" className="text-gray-400 hover:text-white transition">
                Trades
              </a>
              <a href="/learn" className="text-gray-400 hover:text-white transition">
                Belajar
              </a>
              <a href="/settings" className="text-gray-400 hover:text-white transition">
                Settings
              </a>
            </div>
          </nav>
          <main className="p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
