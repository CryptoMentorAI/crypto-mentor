from typing import Optional
import pandas as pd

from .base import BaseStrategy, Signal


class TechnicalAnalysisStrategy(BaseStrategy):
    """
    Strategy berdasarkan Technical Analysis indicators:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - EMA Crossover (9/21)
    - Bollinger Bands
    - Volume confirmation
    """

    name = "technical_analysis"
    description = "RSI, MACD, EMA crossover, Bollinger Bands, Volume analysis"

    def __init__(self, params: dict = None):
        self.params = params or {
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "rsi_period": 14,
            "ema_fast": 9,
            "ema_slow": 21,
        }

    async def analyze(
        self, df: pd.DataFrame, indicators: dict, pair: str, timeframe: str
    ) -> Optional[Signal]:
        if df is None or len(df) < 50:
            return None

        price = indicators["price"]
        rsi = indicators["rsi"]
        macd = indicators["macd"]
        macd_signal = indicators["macd_signal"]
        macd_hist = indicators["macd_histogram"]
        ema_9 = indicators["ema_9"]
        ema_21 = indicators["ema_21"]
        bb_lower = indicators["bb_lower"]
        bb_upper = indicators["bb_upper"]
        volume = indicators["volume"]
        avg_volume = indicators["avg_volume"]
        support = indicators["support"]
        resistance = indicators["resistance"]
        atr = indicators["atr"]

        # ─── BUY Signal Analysis ──────────────────
        buy_reasons = []
        buy_learning = []
        buy_confidence = 0

        # 1. RSI Oversold
        if rsi < self.params["rsi_oversold"]:
            buy_reasons.append(
                f"RSI({self.params['rsi_period']}) = {rsi} → Oversold territory (bawah {self.params['rsi_oversold']}). "
                f"Ini bermakna ramai orang dah jual, dan harga mungkin nak bounce naik."
            )
            buy_learning.append(
                "RSI bawah 30 = oversold. Macam spring yang dah compress — boleh bounce balik. "
                "Tapi jangan rely RSI je, kena ada confirmation lain."
            )
            buy_confidence += 1

        # 2. MACD Bullish Crossover
        prev_hist = df["macd_histogram"].iloc[-2] if "macd_histogram" in df.columns else 0
        if macd_hist > 0 and prev_hist <= 0:
            buy_reasons.append(
                f"MACD histogram baru je cross ke positif ({round(macd_hist, 4)}) → Momentum shift ke bullish. "
                f"MACD line ({round(macd, 4)}) cross atas signal line ({round(macd_signal, 4)})."
            )
            buy_learning.append(
                "MACD crossover = momentum bertukar. Bila histogram dari negatif jadi positif, "
                "bermakna buyer dah mula ambil alih dari seller."
            )
            buy_confidence += 1
        elif macd_hist > 0:
            buy_reasons.append(
                f"MACD histogram positif ({round(macd_hist, 4)}) → Momentum masih bullish."
            )
            buy_confidence += 0.5

        # 3. EMA Crossover (fast above slow = bullish)
        prev_ema9 = df["ema_9"].iloc[-2] if "ema_9" in df.columns else 0
        prev_ema21 = df["ema_21"].iloc[-2] if "ema_21" in df.columns else 0
        if ema_9 > ema_21 and prev_ema9 <= prev_ema21:
            buy_reasons.append(
                f"EMA 9 ({round(ema_9, 2)}) baru cross atas EMA 21 ({round(ema_21, 2)}) → Golden crossover! "
                f"Short-term trend dah bullish."
            )
            buy_learning.append(
                "EMA crossover: Bila EMA cepat (9) cross atas EMA lambat (21), "
                "ini signal yang trend short-term dah berubah ke bullish. "
                "Lagi besar gap antara 2 EMA, lagi kuat trend."
            )
            buy_confidence += 1
        elif ema_9 > ema_21:
            buy_confidence += 0.5

        # 4. Price near Bollinger Band lower
        if price <= bb_lower * 1.01:  # Within 1% of lower band
            buy_reasons.append(
                f"Harga ({price}) dekat dengan Bollinger Band bawah ({round(bb_lower, 2)}) → "
                f"Harga dah stretched ke bawah, potential mean reversion."
            )
            buy_learning.append(
                "Bollinger Bands tunjuk volatility. Bila harga sentuh band bawah, "
                "ia macam rubber band yang dah stretch — ada tendency nak balik ke middle band."
            )
            buy_confidence += 1

        # 5. Volume confirmation
        if volume > avg_volume * 1.5:
            buy_reasons.append(
                f"Volume ({round(volume, 2)}) spike {round(volume / avg_volume, 1)}x dari average ({round(avg_volume, 2)}) → "
                f"Ada minat belian yang kuat!"
            )
            buy_learning.append(
                "Volume = tenaga di sebalik pergerakan harga. "
                "Kalau harga naik tapi volume rendah, pergerakan tu tak kuat. "
                "Volume tinggi confirm bahawa ramai trader sokong pergerakan ni."
            )
            buy_confidence += 1

        # ─── SELL Signal Analysis ─────────────────
        sell_reasons = []
        sell_learning = []
        sell_confidence = 0

        # 1. RSI Overbought
        if rsi > self.params["rsi_overbought"]:
            sell_reasons.append(
                f"RSI({self.params['rsi_period']}) = {rsi} → Overbought territory (atas {self.params['rsi_overbought']}). "
                f"Ramai orang dah beli, harga mungkin nak turun."
            )
            sell_learning.append(
                "RSI atas 70 = overbought. Harga dah naik banyak, potential untuk pullback. "
                "Tapi dalam strong uptrend, RSI boleh stay overbought lama — so kena ada confirmation lain."
            )
            sell_confidence += 1

        # 2. MACD Bearish Crossover
        if macd_hist < 0 and prev_hist >= 0:
            sell_reasons.append(
                f"MACD histogram baru cross ke negatif ({round(macd_hist, 4)}) → Momentum shift ke bearish."
            )
            sell_learning.append(
                "MACD bearish crossover = momentum buyer dah melemah, seller mula ambil alih."
            )
            sell_confidence += 1
        elif macd_hist < 0:
            sell_confidence += 0.5

        # 3. EMA Death Cross
        if ema_9 < ema_21 and prev_ema9 >= prev_ema21:
            sell_reasons.append(
                f"EMA 9 ({round(ema_9, 2)}) baru cross bawah EMA 21 ({round(ema_21, 2)}) → Death cross! "
                f"Short-term trend dah bearish."
            )
            sell_learning.append(
                "Death cross: Bila EMA cepat turun bawah EMA lambat, "
                "ini signal bahawa seller dah take over. Harga likely nak turun lagi."
            )
            sell_confidence += 1

        # 4. Price near Bollinger Band upper
        if price >= bb_upper * 0.99:
            sell_reasons.append(
                f"Harga ({price}) dekat Bollinger Band atas ({round(bb_upper, 2)}) → Stretched ke atas."
            )
            sell_learning.append(
                "Harga di Bollinger Band atas = dah extend sangat. "
                "Biasanya harga akan retrace balik ke middle band."
            )
            sell_confidence += 1

        # 5. Volume on sell
        if volume > avg_volume * 1.5 and sell_confidence >= 1:
            sell_reasons.append(
                f"Volume spike {round(volume / avg_volume, 1)}x → Tekanan jualan kuat."
            )
            sell_confidence += 1

        # ─── Decide: BUY, SELL, or nothing ───────

        if buy_confidence >= 2.5 and buy_confidence > sell_confidence:
            sl = round(support - atr * 0.5, 2) if atr else round(price * 0.99, 2)
            tp = round(resistance, 2) if resistance > price else round(price * 1.02, 2)

            return Signal(
                action="BUY",
                pair=pair,
                price=price,
                strategy=self.name,
                timeframe=timeframe,
                confidence=min(5, int(buy_confidence)),
                stop_loss=sl,
                take_profit=tp,
                reasons=buy_reasons,
                indicators=indicators,
                learning_points=buy_learning,
            )

        if sell_confidence >= 2.5 and sell_confidence > buy_confidence:
            sl = round(resistance + atr * 0.5, 2) if atr else round(price * 1.01, 2)
            tp = round(support, 2) if support < price else round(price * 0.98, 2)

            return Signal(
                action="SELL",
                pair=pair,
                price=price,
                strategy=self.name,
                timeframe=timeframe,
                confidence=min(5, int(sell_confidence)),
                stop_loss=sl,
                take_profit=tp,
                reasons=sell_reasons,
                indicators=indicators,
                learning_points=sell_learning,
            )

        return None
