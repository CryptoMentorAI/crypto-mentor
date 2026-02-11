import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import Signal
from .technical import TechnicalAnalysisStrategy
from .price_action import PriceActionStrategy
from .trend import TrendFollowingStrategy
from .scalping import ScalpingStrategy
from backend.database.models import StrategyConfig


class StrategyOrchestrator:
    """
    Combine signals dari semua strategy, score confluence,
    dan decide trade terbaik.
    """

    def __init__(self):
        self.strategies = {
            "technical_analysis": TechnicalAnalysisStrategy(),
            "price_action": PriceActionStrategy(),
            "trend_following": TrendFollowingStrategy(),
            "scalping": ScalpingStrategy(),
        }
        self._last_signal_time: Optional[float] = None
        self._cooldown_seconds = 300  # 5 min cooldown between trades

    async def load_configs(self, session: AsyncSession):
        """Load strategy configurations from database."""
        result = await session.execute(select(StrategyConfig))
        configs = result.scalars().all()

        for config in configs:
            if config.name in self.strategies:
                self.strategies[config.name].params = config.parameters
                if not config.enabled:
                    del self.strategies[config.name]

    async def analyze_all(self, df, indicators: dict, pair: str, timeframe: str) -> Optional[Signal]:
        """Run all enabled strategies and return best signal based on confluence."""
        import time

        # Cooldown check
        if self._last_signal_time:
            elapsed = time.time() - self._last_signal_time
            if elapsed < self._cooldown_seconds:
                return None

        signals: list[Signal] = []

        # Run all strategies concurrently
        tasks = []
        for name, strategy in self.strategies.items():
            tasks.append(self._run_strategy(strategy, df, indicators, pair, timeframe))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Signal):
                signals.append(result)

        if not signals:
            return None

        # ─── Confluence Analysis ─────────────────

        buy_signals = [s for s in signals if s.action == "BUY"]
        sell_signals = [s for s in signals if s.action == "SELL"]

        best_signal = None

        if len(buy_signals) > len(sell_signals) and buy_signals:
            best_signal = self._merge_signals(buy_signals, "BUY")
        elif len(sell_signals) > len(buy_signals) and sell_signals:
            best_signal = self._merge_signals(sell_signals, "SELL")
        elif buy_signals and sell_signals:
            # Conflicting signals — go with higher total confidence
            buy_conf = sum(s.confidence for s in buy_signals)
            sell_conf = sum(s.confidence for s in sell_signals)
            if buy_conf > sell_conf:
                best_signal = self._merge_signals(buy_signals, "BUY")
            elif sell_conf > buy_conf:
                best_signal = self._merge_signals(sell_signals, "SELL")
            # If equal, skip — conflicting signals = no trade

        if best_signal and best_signal.confidence >= 3:
            self._last_signal_time = time.time()
            return best_signal

        return None

    async def _run_strategy(self, strategy, df, indicators, pair, timeframe) -> Optional[Signal]:
        try:
            return await strategy.analyze(df, indicators, pair, timeframe)
        except Exception as e:
            print(f"Strategy {strategy.name} error: {e}")
            return None

    def _merge_signals(self, signals: list[Signal], action: str) -> Signal:
        """Merge multiple signals into one confluence signal."""
        # Take the signal with highest confidence as base
        base = max(signals, key=lambda s: s.confidence)

        # Combine all reasons and learning points
        all_reasons = []
        all_learning = []
        strategy_names = []

        for s in signals:
            all_reasons.extend(s.reasons)
            all_learning.extend(s.learning_points)
            strategy_names.append(s.strategy)

        # Boost confidence based on number of agreeing strategies
        confluence_bonus = len(signals) - 1  # Extra confidence for each additional strategy
        total_confidence = min(5, base.confidence + confluence_bonus)

        # Add confluence explanation
        if len(signals) > 1:
            all_reasons.insert(0,
                f"CONFLUENCE: {len(signals)} strategy setuju — {', '.join(strategy_names)}! "
                f"Bila multiple strategy bagi signal sama, confidence level tinggi."
            )
            all_learning.insert(0,
                f"Confluence = beberapa analysis method agree pada satu arah. "
                f"Ini konsep paling penting dalam trading: JANGAN trade based on 1 indicator je. "
                f"Lagi banyak 'confluences', lagi tinggi probability trade berjaya. "
                f"Sekarang ada {len(signals)} confluences — ini {'sangat kuat' if len(signals) >= 3 else 'kuat'}!"
            )

        return Signal(
            action=action,
            pair=base.pair,
            price=base.price,
            strategy=" + ".join(strategy_names),
            timeframe=base.timeframe,
            confidence=total_confidence,
            stop_loss=base.stop_loss,
            take_profit=base.take_profit,
            reasons=all_reasons,
            indicators=base.indicators,
            learning_points=all_learning,
        )


# Singleton
orchestrator = StrategyOrchestrator()
