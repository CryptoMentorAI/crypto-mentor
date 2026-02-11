from typing import Optional
import pandas as pd

from .base import BaseStrategy, Signal


class TrendFollowingStrategy(BaseStrategy):
    """
    Strategy berdasarkan Trend Following:
    - Moving Average Ribbon (EMA 9/21/50/200 alignment)
    - ADX (Average Directional Index) — trend strength
    - Higher Highs / Higher Lows pattern
    - Trend Channel
    """

    name = "trend_following"
    description = "MA Ribbon, ADX trend strength, Higher highs/lows"

    def __init__(self, params: dict = None):
        self.params = params or {
            "adx_threshold": 25,
            "ma_ribbon": [9, 21, 50, 200],
            "trend_confirmation_candles": 3,
        }

    async def analyze(
        self, df: pd.DataFrame, indicators: dict, pair: str, timeframe: str
    ) -> Optional[Signal]:
        if df is None or len(df) < 200:
            return None

        price = indicators["price"]
        ema_9 = indicators["ema_9"]
        ema_21 = indicators["ema_21"]
        ema_50 = indicators["ema_50"]
        ema_200 = indicators["ema_200"]
        adx = indicators["adx"]
        atr = indicators["atr"]
        support = indicators["support"]
        resistance = indicators["resistance"]

        reasons = []
        learning = []
        confidence = 0
        action = None

        # ─── MA Ribbon Alignment ─────────────────

        bullish_ribbon = ema_9 > ema_21 > ema_50 > ema_200
        bearish_ribbon = ema_9 < ema_21 < ema_50 < ema_200

        if bullish_ribbon:
            reasons.append(
                f"MA Ribbon perfectly aligned BULLISH: EMA9 ({round(ema_9, 2)}) > EMA21 ({round(ema_21, 2)}) "
                f"> EMA50 ({round(ema_50, 2)}) > EMA200 ({round(ema_200, 2)}). "
                f"Semua timeframe trend naik!"
            )
            learning.append(
                "MA Ribbon = susun semua Moving Average dari cepat ke lambat. "
                "Kalau semua align dari atas ke bawah (9 > 21 > 50 > 200), "
                "ini bermakna SEMUA timeframe agree bahawa trend naik. "
                "Ini setup paling kuat untuk trend following. "
                "Tip: Jangan lawan trend bila ribbon aligned — 'trend is your friend'."
            )
            action = "BUY"
            confidence += 2

        elif bearish_ribbon:
            reasons.append(
                f"MA Ribbon perfectly aligned BEARISH: EMA9 ({round(ema_9, 2)}) < EMA21 ({round(ema_21, 2)}) "
                f"< EMA50 ({round(ema_50, 2)}) < EMA200 ({round(ema_200, 2)}). "
                f"Semua timeframe trend turun!"
            )
            learning.append(
                "Bearish ribbon = semua MA align turun. Ini masa yang paling bahaya nak buy "
                "sebab seluruh market structure bearish. Wait for ribbon to flip before buying."
            )
            action = "SELL"
            confidence += 2

        # ─── ADX Trend Strength ──────────────────

        if adx > self.params["adx_threshold"]:
            strength = "KUAT" if adx > 40 else "SEDERHANA"
            reasons.append(
                f"ADX = {round(adx, 2)} → Trend {strength}. "
                f"{'Market trending dengan kuat!' if adx > 40 else 'Market ada trend yang jelas.'}"
            )
            learning.append(
                f"ADX (Average Directional Index) ukur KEKUATAN trend, bukan arah. "
                f"ADX < 20 = market sideways/choppy (jangan trade trend). "
                f"ADX 20-40 = trend sederhana. ADX > 40 = trend sangat kuat. "
                f"Sekarang ADX = {round(adx, 2)}, bermakna trend {'sangat kuat' if adx > 40 else 'ada tapi sederhana'}. "
                f"Tip: Trend following strategy paling berkesan bila ADX > 25."
            )
            confidence += 1
        else:
            reasons.append(
                f"ADX = {round(adx, 2)} → Market SIDEWAYS (bawah {self.params['adx_threshold']}). "
                f"Trend following tak sesuai sekarang."
            )
            learning.append(
                "ADX rendah bermakna market tak trending — ia choppy/sideways. "
                "Dalam keadaan ni, trend following strategy akan bagi banyak false signals. "
                "Better guna mean reversion atau tunggu trend develop."
            )
            confidence -= 1

        # ─── Higher Highs / Higher Lows ──────────

        hh_hl = self._detect_higher_highs_lows(df)
        if hh_hl:
            reasons.append(hh_hl["reason"])
            learning.append(hh_hl["learning"])
            if hh_hl["bias"] == action or action is None:
                confidence += hh_hl["weight"]
                action = action or hh_hl["bias"]

        # ─── Price position relative to EMAs ─────

        if price > ema_21 and action == "BUY":
            reasons.append(
                f"Harga ({price}) atas EMA21 ({round(ema_21, 2)}) — "
                f"sedang pullback ke EMA sebagai support. Good entry point!"
            )
            learning.append(
                "Dalam uptrend, EMA21 sering jadi 'dynamic support' — harga bounce dari situ. "
                "Strategy: tunggu harga pullback ke EMA21, then buy. "
                "Ini dipanggil 'buying the dip in an uptrend'."
            )
            confidence += 0.5

        # ─── Generate Signal ─────────────────────

        if confidence >= 2.5 and action:
            if action == "BUY":
                sl = round(ema_50 - atr * 0.5, 2) if atr else round(price * 0.98, 2)
                tp = round(price + (price - sl) * 2, 2)  # 2:1 R:R
            else:
                sl = round(ema_50 + atr * 0.5, 2) if atr else round(price * 1.02, 2)
                tp = round(price - (sl - price) * 2, 2)

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

    def _detect_higher_highs_lows(self, df: pd.DataFrame) -> Optional[dict]:
        """Detect Higher Highs / Higher Lows or Lower Highs / Lower Lows pattern."""
        n = self.params["trend_confirmation_candles"]
        if len(df) < n * 10:
            return None

        # Find swing highs and lows using simple pivot detection
        highs = []
        lows = []

        for i in range(5, len(df) - 5, 5):
            window = df.iloc[i - 5 : i + 5]
            if df.iloc[i]["high"] == window["high"].max():
                highs.append(df.iloc[i]["high"])
            if df.iloc[i]["low"] == window["low"].min():
                lows.append(df.iloc[i]["low"])

        if len(highs) < 3 or len(lows) < 3:
            return None

        recent_highs = highs[-3:]
        recent_lows = lows[-3:]

        hh = all(recent_highs[i] > recent_highs[i - 1] for i in range(1, len(recent_highs)))
        hl = all(recent_lows[i] > recent_lows[i - 1] for i in range(1, len(recent_lows)))
        lh = all(recent_highs[i] < recent_highs[i - 1] for i in range(1, len(recent_highs)))
        ll = all(recent_lows[i] < recent_lows[i - 1] for i in range(1, len(recent_lows)))

        if hh and hl:
            return {
                "reason": (
                    f"Higher Highs + Higher Lows detected! "
                    f"Highs: {[round(h, 2) for h in recent_highs]}, Lows: {[round(l, 2) for l in recent_lows]}. "
                    f"Market structure bullish — setiap swing naik lebih tinggi dari sebelumnya."
                ),
                "learning": (
                    "Higher Highs (HH) + Higher Lows (HL) = UPTREND confirmed. "
                    "Ini asas paling basic market structure: "
                    "- HH = setiap puncak lebih tinggi dari puncak sebelumnya "
                    "- HL = setiap lembah lebih tinggi dari lembah sebelumnya "
                    "Selagi pattern ni kekal, trend masih bullish. "
                    "Trend break bila harga buat Lower Low — ini signal pertama trend mungkin berubah."
                ),
                "weight": 1.5,
                "bias": "BUY",
            }

        if lh and ll:
            return {
                "reason": (
                    f"Lower Highs + Lower Lows detected! "
                    f"Highs: {[round(h, 2) for h in recent_highs]}, Lows: {[round(l, 2) for l in recent_lows]}. "
                    f"Market structure bearish."
                ),
                "learning": (
                    "Lower Highs (LH) + Lower Lows (LL) = DOWNTREND. "
                    "Setiap bounce makin rendah, setiap drop pun makin rendah. "
                    "Jangan cuba 'catch the falling knife' — tunggu market structure break dulu "
                    "(bila harga buat Higher High)."
                ),
                "weight": 1.5,
                "bias": "SELL",
            }

        return None
