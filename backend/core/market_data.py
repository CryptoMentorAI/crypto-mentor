import asyncio
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import ccxt.async_support as ccxt
import pandas as pd
import ta as ta_lib

from backend.core.config import settings


class MarketDataEngine:
    """Fetch and manage market data from Bybit or mock data."""

    def __init__(self):
        self.exchange: Optional[ccxt.bybit] = None
        self.mock_mode = settings.MOCK_MODE
        self._mock_price = 67500.0  # Starting BTC price for mock
        self._mock_base_time = datetime.now(timezone.utc)
        self._candle_cache: dict[str, pd.DataFrame] = {}
        self._price_listeners: list = []

    async def initialize(self):
        """Connect to Bybit testnet or setup mock mode."""
        if not self.mock_mode and settings.is_bybit_configured:
            self.exchange = ccxt.bybit({
                "apiKey": settings.BYBIT_API_KEY,
                "secret": settings.BYBIT_API_SECRET,
                "sandbox": True,  # Testnet mode
                "options": {"defaultType": "spot"},
            })
            print("Connected to Bybit Testnet")
        else:
            self.mock_mode = True
            print("Running in mock data mode")

    async def close(self):
        if self.exchange:
            await self.exchange.close()

    def add_price_listener(self, callback):
        self._price_listeners.append(callback)

    async def _notify_price(self, pair: str, price: float, timestamp: str):
        for listener in self._price_listeners:
            try:
                await listener(pair, price, timestamp)
            except Exception:
                pass

    # ─── Price Data ────────────────────────────────────────

    async def get_current_price(self, pair: str = None) -> float:
        pair = pair or settings.DEFAULT_PAIR
        if self.mock_mode:
            return self._generate_mock_price()

        ticker = await self.exchange.fetch_ticker(pair)
        return ticker["last"]

    async def get_candles(
        self, pair: str = None, timeframe: str = None, limit: int = 200
    ) -> pd.DataFrame:
        """Fetch OHLCV candles and return as DataFrame with TA indicators."""
        pair = pair or settings.DEFAULT_PAIR
        timeframe = timeframe or settings.DEFAULT_TIMEFRAME

        cache_key = f"{pair}_{timeframe}"

        if self.mock_mode:
            df = self._generate_mock_candles(limit, timeframe)
        else:
            ohlcv = await self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        # Calculate technical indicators
        df = self._add_indicators(df)

        self._candle_cache[cache_key] = df
        return df

    async def get_indicators(self, pair: str = None, timeframe: str = None) -> dict:
        """Get current indicator values as a dictionary."""
        df = await self.get_candles(pair, timeframe)
        last = df.iloc[-1]

        return {
            "price": last["close"],
            "rsi": round(last.get("rsi", 50), 2),
            "macd": round(last.get("macd", 0), 4),
            "macd_signal": round(last.get("macd_signal", 0), 4),
            "macd_histogram": round(last.get("macd_histogram", 0), 4),
            "ema_9": round(last.get("ema_9", 0), 2),
            "ema_21": round(last.get("ema_21", 0), 2),
            "ema_50": round(last.get("ema_50", 0), 2),
            "ema_200": round(last.get("ema_200", 0), 2),
            "bb_upper": round(last.get("bb_upper", 0), 2),
            "bb_middle": round(last.get("bb_middle", 0), 2),
            "bb_lower": round(last.get("bb_lower", 0), 2),
            "volume": last["volume"],
            "avg_volume": round(df["volume"].tail(20).mean(), 2),
            "atr": round(last.get("atr", 0), 2),
            "adx": round(last.get("adx", 0), 2),
            "support": self._find_support(df),
            "resistance": self._find_resistance(df),
        }

    # ─── Technical Indicators ─────────────────────────────

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators to the dataframe."""
        n = len(df)

        # RSI (needs ~15 rows)
        if n >= 15:
            df["rsi"] = ta_lib.momentum.RSIIndicator(df["close"], window=14).rsi()
        else:
            df["rsi"] = 50.0

        # MACD (needs ~27 rows)
        if n >= 27:
            macd_ind = ta_lib.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
            df["macd"] = macd_ind.macd()
            df["macd_histogram"] = macd_ind.macd_diff()
            df["macd_signal"] = macd_ind.macd_signal()
        else:
            df["macd"] = 0.0
            df["macd_histogram"] = 0.0
            df["macd_signal"] = 0.0

        # EMAs
        for period, col in [(9, "ema_9"), (21, "ema_21"), (50, "ema_50"), (200, "ema_200")]:
            if n >= period:
                df[col] = ta_lib.trend.EMAIndicator(df["close"], window=period).ema_indicator()
            else:
                df[col] = df["close"]

        # Bollinger Bands (needs ~20 rows)
        if n >= 20:
            bb = ta_lib.volatility.BollingerBands(df["close"], window=20, window_dev=2)
            df["bb_lower"] = bb.bollinger_lband()
            df["bb_middle"] = bb.bollinger_mavg()
            df["bb_upper"] = bb.bollinger_hband()
        else:
            df["bb_lower"] = df["close"] * 0.98
            df["bb_middle"] = df["close"]
            df["bb_upper"] = df["close"] * 1.02

        # ATR (needs ~15 rows)
        if n >= 15:
            df["atr"] = ta_lib.volatility.AverageTrueRange(
                df["high"], df["low"], df["close"], window=14
            ).average_true_range()
        else:
            df["atr"] = (df["high"] - df["low"]).mean()

        # ADX (needs ~28 rows)
        if n >= 28:
            df["adx"] = ta_lib.trend.ADXIndicator(
                df["high"], df["low"], df["close"], window=14
            ).adx()
        else:
            df["adx"] = 20.0

        # Volume SMA
        df["vol_sma"] = df["volume"].rolling(window=min(20, n)).mean()

        return df

    def _find_support(self, df: pd.DataFrame, lookback: int = 50) -> float:
        """Find nearest support level from recent lows."""
        recent = df.tail(lookback)
        lows = recent["low"].values
        # Simple approach: find clusters of lows
        sorted_lows = sorted(lows)
        # Return the 10th percentile as approximate support
        idx = max(0, len(sorted_lows) // 10)
        return round(sorted_lows[idx], 2)

    def _find_resistance(self, df: pd.DataFrame, lookback: int = 50) -> float:
        """Find nearest resistance level from recent highs."""
        recent = df.tail(lookback)
        highs = recent["high"].values
        sorted_highs = sorted(highs, reverse=True)
        idx = max(0, len(sorted_highs) // 10)
        return round(sorted_highs[idx], 2)

    # ─── Mock Data Generation ────────────────────────────

    def _generate_mock_price(self) -> float:
        """Generate realistic-ish price movement."""
        change = random.gauss(0, 50)  # Mean 0, std $50
        self._mock_price += change
        self._mock_price = max(self._mock_price, 20000)  # Floor
        return round(self._mock_price, 2)

    def _generate_mock_candles(self, limit: int, timeframe: str) -> pd.DataFrame:
        """Generate realistic mock OHLCV data."""
        tf_minutes = self._timeframe_to_minutes(timeframe)
        now = datetime.now(timezone.utc)
        data = []

        price = 65000.0
        base_volume = 1000.0

        for i in range(limit):
            ts = now - timedelta(minutes=tf_minutes * (limit - i))
            # Random walk with slight upward bias
            change_pct = random.gauss(0.0001, 0.005)
            price *= 1 + change_pct

            high = price * (1 + abs(random.gauss(0, 0.003)))
            low = price * (1 - abs(random.gauss(0, 0.003)))
            open_price = price * (1 + random.gauss(0, 0.001))
            volume = base_volume * (1 + abs(random.gauss(0, 0.5)))

            data.append({
                "timestamp": ts,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(price, 2),
                "volume": round(volume, 2),
            })

        self._mock_price = price
        return pd.DataFrame(data)

    def _timeframe_to_minutes(self, tf: str) -> int:
        mapping = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "1d": 1440,
        }
        return mapping.get(tf, 15)

    # ─── Price Stream (for real-time updates) ─────────────

    async def stream_prices(self, pair: str = None, interval: float = 5.0):
        """Stream price updates — mock or real."""
        pair = pair or settings.DEFAULT_PAIR

        while True:
            try:
                price = await self.get_current_price(pair)
                ts = datetime.now(timezone.utc).isoformat()
                await self._notify_price(pair, price, ts)
            except Exception as e:
                print(f"Price stream error: {e}")
            await asyncio.sleep(interval)


# Singleton instance
market_data = MarketDataEngine()
