from typing import Optional
import pandas as pd

from .base import BaseStrategy, Signal


class ScalpingStrategy(BaseStrategy):
    """
    Scalping Strategy — Quick trades, small profits:
    - Quick RSI divergence on short timeframe
    - VWAP deviation
    - Micro support/resistance
    - Volume surge detection
    """

    name = "scalping"
    description = "Quick RSI, VWAP deviation, Micro S/R, Volume surge"

    def __init__(self, params: dict = None):
        self.params = params or {
            "rsi_period": 7,
            "vwap_deviation": 0.002,
            "min_volume_ratio": 1.5,
            "quick_tp_percent": 0.3,
        }

    async def analyze(
        self, df: pd.DataFrame, indicators: dict, pair: str, timeframe: str
    ) -> Optional[Signal]:
        if df is None or len(df) < 30:
            return None

        price = indicators["price"]
        rsi = indicators["rsi"]
        volume = indicators["volume"]
        avg_volume = indicators["avg_volume"]
        support = indicators["support"]
        resistance = indicators["resistance"]
        bb_lower = indicators["bb_lower"]
        bb_upper = indicators["bb_upper"]
        bb_middle = indicators.get("bb_middle", (bb_upper + bb_lower) / 2)
        atr = indicators["atr"]

        reasons = []
        learning = []
        confidence = 0
        action = None

        # ─── Quick RSI (period 7 for scalping) ──

        # Calculate quick RSI from raw data
        import ta as ta_lib
        quick_rsi = ta_lib.momentum.RSIIndicator(df["close"], window=self.params["rsi_period"]).rsi()
        if quick_rsi is not None and len(quick_rsi) > 0:
            qrsi = round(quick_rsi.iloc[-1], 2) if not pd.isna(quick_rsi.iloc[-1]) else 50

            if qrsi < 20:
                reasons.append(
                    f"Quick RSI(7) = {qrsi} → Extreme oversold! "
                    f"Dalam short timeframe, ini biasanya bounce cepat."
                )
                learning.append(
                    "Untuk scalping, kita guna RSI period pendek (7 instead of 14). "
                    "RSI(7) lebih sensitive — cepat detect oversold/overbought. "
                    "RSI(7) < 20 = extreme oversold, expect quick bounce. "
                    "Tapi risk tinggi sebab boleh stay oversold dalam strong downtrend."
                )
                action = "BUY"
                confidence += 1.5

            elif qrsi > 80:
                reasons.append(
                    f"Quick RSI(7) = {qrsi} → Extreme overbought! Quick pullback expected."
                )
                learning.append(
                    "RSI(7) > 80 = extreme overbought dalam short term. "
                    "Expect quick pullback. Scalper akan take profit sini."
                )
                action = "SELL"
                confidence += 1.5

        # ─── Bollinger Band Squeeze & Bounce ─────

        bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle else 0

        if price <= bb_lower * 1.002:
            reasons.append(
                f"Harga ({price}) touch Bollinger Band bawah ({round(bb_lower, 2)}). "
                f"Quick bounce ke middle band ({round(bb_middle, 2)}) expected."
            )
            learning.append(
                "Scalping dengan Bollinger Bands: Bila harga touch band bawah, "
                "target quick profit ke middle band (SMA20). "
                "Ini bukan trade besar — just quick in-and-out. "
                f"BB Width sekarang: {round(bb_width, 4)} — "
                f"{'Squeeze (low volatility) = breakout coming!' if bb_width < 0.02 else 'Normal volatility.'}"
            )
            if action != "SELL":
                action = "BUY"
                confidence += 1

        elif price >= bb_upper * 0.998:
            reasons.append(
                f"Harga ({price}) touch Bollinger Band atas ({round(bb_upper, 2)}). "
                f"Quick pullback ke middle band expected."
            )
            learning.append(
                "Scalping BB: Touch band atas → expect pullback ke middle band. "
                "Quick scalp profit, jangan greedy."
            )
            if action != "BUY":
                action = "SELL"
                confidence += 1

        # ─── Volume Surge ────────────────────────

        vol_ratio = volume / avg_volume if avg_volume > 0 else 1

        if vol_ratio > self.params["min_volume_ratio"]:
            reasons.append(
                f"Volume SURGE! {round(vol_ratio, 1)}x dari average. "
                f"Big players sedang bergerak — ikut arah volume."
            )
            learning.append(
                "Volume surge dalam scalping = 'smart money' sedang masuk. "
                "Kalau volume spike + harga naik = institutional buying. "
                "Kalau volume spike + harga turun = institutional selling. "
                "Scalper ikut je arah big players — jangan lawan."
            )
            confidence += 1

        # ─── Micro Support/Resistance ────────────

        # Use recent 20-candle high/low as micro levels
        micro_high = df["high"].tail(20).max()
        micro_low = df["low"].tail(20).min()

        if abs(price - micro_low) / price < 0.003 and action != "SELL":
            reasons.append(
                f"Harga dekat micro support ({round(micro_low, 2)}) — low 20 candles terakhir."
            )
            learning.append(
                "Micro S/R = support/resistance dari timeframe kecil (recent 20 candles). "
                "Untuk scalping, micro levels cukup — tak perlu tengok daily level pun."
            )
            action = action or "BUY"
            confidence += 0.5

        elif abs(price - micro_high) / price < 0.003 and action != "BUY":
            reasons.append(
                f"Harga dekat micro resistance ({round(micro_high, 2)}) — high 20 candles terakhir."
            )
            action = action or "SELL"
            confidence += 0.5

        # ─── Generate Signal ─────────────────────

        if confidence >= 2 and action:
            tp_pct = self.params["quick_tp_percent"] / 100
            sl_pct = tp_pct * 0.7  # Tighter stop for scalps

            if action == "BUY":
                sl = round(price * (1 - sl_pct), 2)
                tp = round(price * (1 + tp_pct), 2)
            else:
                sl = round(price * (1 + sl_pct), 2)
                tp = round(price * (1 - tp_pct), 2)

            return Signal(
                action=action,
                pair=pair,
                price=price,
                strategy=self.name,
                timeframe=timeframe,
                confidence=min(5, int(confidence)),
                stop_loss=sl,
                take_profit=tp,
                reasons=reasons,
                indicators=indicators,
                learning_points=learning,
            )

        return None
