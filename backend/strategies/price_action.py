from typing import Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal


class PriceActionStrategy(BaseStrategy):
    """
    Strategy berdasarkan Price Action:
    - Support/Resistance levels
    - Candlestick patterns (Engulfing, Hammer, Doji, etc.)
    - Breakout detection
    - Supply/Demand zones
    """

    name = "price_action"
    description = "Support/Resistance, Candlestick patterns, Breakout detection"

    def __init__(self, params: dict = None):
        self.params = params or {
            "support_lookback": 50,
            "resistance_lookback": 50,
            "min_touches": 2,
            "breakout_threshold": 0.005,
        }

    async def analyze(
        self, df: pd.DataFrame, indicators: dict, pair: str, timeframe: str
    ) -> Optional[Signal]:
        if df is None or len(df) < 30:
            return None

        price = indicators["price"]
        support = indicators["support"]
        resistance = indicators["resistance"]
        atr = indicators["atr"]
        volume = indicators["volume"]
        avg_volume = indicators["avg_volume"]

        reasons = []
        learning = []
        confidence = 0
        action = None

        # ─── Candlestick Pattern Detection ───────

        pattern = self._detect_candlestick_pattern(df)
        if pattern:
            reasons.append(pattern["reason"])
            learning.append(pattern["learning"])
            confidence += pattern["weight"]
            action = pattern["bias"]  # "BUY" or "SELL"

        # ─── Support/Resistance Proximity ────────

        price_to_support = abs(price - support) / price
        price_to_resistance = abs(price - resistance) / price

        if price_to_support < 0.01:  # Within 1% of support
            reasons.append(
                f"Harga ({price}) sangat dekat dengan support level ({support}) — "
                f"hanya {round(price_to_support * 100, 2)}% jauhnya. "
                f"Support ni level dimana buyer selalu masuk."
            )
            learning.append(
                "Support level = lantai harga. Harga cenderung untuk bounce dari support "
                "sebab ramai trader letak buy order kat situ. Lagi banyak kali harga test "
                "support tanpa break, lagi kuat level tu."
            )
            if action != "SELL":
                action = "BUY"
                confidence += 1.5

        elif price_to_resistance < 0.01:  # Within 1% of resistance
            reasons.append(
                f"Harga ({price}) sangat dekat dengan resistance level ({resistance}) — "
                f"hanya {round(price_to_resistance * 100, 2)}% jauhnya. "
                f"Resistance ni level dimana seller biasa masuk."
            )
            learning.append(
                "Resistance level = siling harga. Harga cenderung untuk reject dari resistance "
                "sebab ramai trader letak sell order kat situ. Kalau break resistance dengan "
                "volume tinggi, ia jadi support baru — ini dipanggil 'flip'."
            )
            if action != "BUY":
                action = "SELL"
                confidence += 1.5

        # ─── Breakout Detection ──────────────────

        breakout = self._detect_breakout(df, resistance, support)
        if breakout:
            reasons.append(breakout["reason"])
            learning.append(breakout["learning"])
            confidence += breakout["weight"]
            action = breakout["bias"]

        # ─── Volume Confirmation ─────────────────

        if volume > avg_volume * 1.5 and action:
            reasons.append(
                f"Volume ({round(volume, 2)}) {round(volume / avg_volume, 1)}x lebih tinggi dari average → "
                f"Confirm pergerakan harga ni ada tenaga."
            )
            learning.append(
                "Dalam price action, volume confirm intention. Breakout tanpa volume = fake breakout. "
                "Bounce dari support dengan volume tinggi = bounce yang kuat."
            )
            confidence += 1

        # ─── Generate Signal ─────────────────────

        if confidence >= 2 and action:
            if action == "BUY":
                sl = round(support - (atr or price * 0.005), 2)
                tp = round(resistance, 2) if resistance > price else round(price * 1.02, 2)
            else:
                sl = round(resistance + (atr or price * 0.005), 2)
                tp = round(support, 2) if support < price else round(price * 0.98, 2)

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

    def _detect_candlestick_pattern(self, df: pd.DataFrame) -> Optional[dict]:
        """Detect common candlestick patterns on the last few candles."""
        if len(df) < 3:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        o, h, l, c = last["open"], last["high"], last["low"], last["close"]
        po, ph, pl, pc = prev["open"], prev["high"], prev["low"], prev["close"]

        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l if h != l else 0.001

        # ── Bullish Engulfing ──
        if pc < po and c > o and c > po and o < pc:
            return {
                "reason": (
                    f"Bullish Engulfing pattern detected! Candle hijau sekarang (O:{round(o, 2)} C:{round(c, 2)}) "
                    f"completely 'menelan' candle merah sebelumnya (O:{round(po, 2)} C:{round(pc, 2)}). "
                    f"Ini tanda kuat buyer dah ambil alih."
                ),
                "learning": (
                    "Bullish Engulfing = candle hijau besar yang menelan candle merah sebelumnya. "
                    "Maknanya buyer datang dengan kuat dan push harga melepasi opening price semalam. "
                    "Pattern ni paling kuat kalau muncul dekat support level."
                ),
                "weight": 1.5,
                "bias": "BUY",
            }

        # ── Bearish Engulfing ──
        if pc > po and c < o and c < po and o > pc:
            return {
                "reason": (
                    f"Bearish Engulfing pattern! Candle merah sekarang menelan candle hijau sebelumnya. "
                    f"Seller dah ambil alih dengan kuat."
                ),
                "learning": (
                    "Bearish Engulfing = opposite of bullish. Candle merah besar telan candle hijau. "
                    "Signal kuat bahawa seller dah dominate. Paling bermakna kalau dekat resistance."
                ),
                "weight": 1.5,
                "bias": "SELL",
            }

        # ── Hammer (bullish reversal) ──
        if lower_wick > body * 2 and upper_wick < body * 0.5 and total_range > 0:
            return {
                "reason": (
                    f"Hammer candlestick pattern! Lower wick panjang ({round(lower_wick, 2)}) "
                    f"dengan body kecil ({round(body, 2)}). Seller push harga turun tapi buyer "
                    f"push balik naik — tanda rejection ke bawah."
                ),
                "learning": (
                    "Hammer = candle dengan ekor bawah panjang, body kecil kat atas. "
                    "Ceritanya: seller cuba push harga turun, tapi buyer fight balik dan "
                    "push harga naik semula. Ini signal reversal bullish, especially dekat support."
                ),
                "weight": 1,
                "bias": "BUY",
            }

        # ── Shooting Star (bearish reversal) ──
        if upper_wick > body * 2 and lower_wick < body * 0.5 and total_range > 0:
            return {
                "reason": (
                    f"Shooting Star pattern! Upper wick panjang ({round(upper_wick, 2)}) — "
                    f"buyer push naik tapi seller reject. Bearish signal."
                ),
                "learning": (
                    "Shooting Star = opposite of Hammer. Ekor atas panjang, body kecil kat bawah. "
                    "Buyer cuba push naik tapi kena reject — seller masih kuat. "
                    "Kalau muncul dekat resistance, very bearish."
                ),
                "weight": 1,
                "bias": "SELL",
            }

        # ── Doji (indecision) ──
        if body < total_range * 0.1 and total_range > 0:
            return {
                "reason": (
                    f"Doji candle detected — open ({round(o, 2)}) dan close ({round(c, 2)}) hampir sama. "
                    f"Market tak pasti arah. Tunggu confirmation."
                ),
                "learning": (
                    "Doji = candle dimana open dan close hampir sama (body sangat kecil). "
                    "Ini tanda indecision — buyer dan seller sama kuat. "
                    "Doji dekat support = potential bullish reversal. "
                    "Doji dekat resistance = potential bearish reversal. "
                    "Jangan trade Doji je — tunggu next candle untuk confirm arah."
                ),
                "weight": 0.5,
                "bias": "BUY" if c > o else "SELL",
            }

        return None

    def _detect_breakout(self, df: pd.DataFrame, resistance: float, support: float) -> Optional[dict]:
        """Detect price breakout above resistance or below support."""
        if len(df) < 3:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]
        threshold = self.params["breakout_threshold"]

        # Bullish breakout above resistance
        if last["close"] > resistance * (1 + threshold) and prev["close"] <= resistance:
            return {
                "reason": (
                    f"BREAKOUT atas resistance {resistance}! Harga ({last['close']}) "
                    f"berjaya break level yang sebelum ni jadi siling. "
                    f"Ini boleh jadi start pergerakan besar ke atas."
                ),
                "learning": (
                    "Breakout = harga berjaya tembus level S/R yang penting. "
                    "Resistance yang di-break jadi support baru (resistance flip). "
                    "Kunci breakout yang valid: (1) close atas resistance, bukan just wick, "
                    "(2) volume tinggi, (3) candle strong (body besar). "
                    "Fake breakout = harga break tapi cepat masuk balik — sebab tu volume penting."
                ),
                "weight": 2,
                "bias": "BUY",
            }

        # Bearish breakdown below support
        if last["close"] < support * (1 - threshold) and prev["close"] >= support:
            return {
                "reason": (
                    f"BREAKDOWN bawah support {support}! Harga ({last['close']}) "
                    f"break level lantai. Ini boleh jadi start pergerakan besar ke bawah."
                ),
                "learning": (
                    "Breakdown = harga jatuh bawah support. Support yang break jadi resistance baru. "
                    "Ini biasanya trigger stop loss ramai orang, yang buat harga jatuh lagi — "
                    "dipanggil 'stop loss cascade'."
                ),
                "weight": 2,
                "bias": "SELL",
            }

        return None
