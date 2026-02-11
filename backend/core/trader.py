from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.database.models import Trade, TradeExplanation, PostAnalysis, MarketSnapshot, Portfolio
from backend.strategies.base import Signal
from backend.explainer.trade_explainer import explainer


class PaperTrader:
    """
    Paper Trading Engine — execute trades on paper (simulated).
    Track portfolio, positions, PnL.
    """

    def __init__(self):
        self.position_size_percent = 5  # Use 5% of balance per trade
        self.max_open_trades = 3

    async def execute_trade(self, signal: Signal, session: AsyncSession) -> Optional[Trade]:
        """Open a new paper trade based on signal."""
        # Check max open trades
        open_trades = await session.execute(
            select(Trade).where(Trade.status == "OPEN")
        )
        if len(open_trades.scalars().all()) >= self.max_open_trades:
            return None

        # Check if we already have a position in this pair
        existing = await session.execute(
            select(Trade).where(Trade.pair == signal.pair, Trade.status == "OPEN")
        )
        if existing.scalars().first():
            return None

        # Get portfolio balance
        portfolio = await self._get_portfolio(session)
        if not portfolio:
            return None

        # Calculate position size
        trade_amount = portfolio.balance * (self.position_size_percent / 100)
        quantity = trade_amount / signal.price

        # Create trade record
        trade = Trade(
            pair=signal.pair,
            side=signal.action,
            entry_price=signal.price,
            quantity=quantity,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            status="OPEN",
            strategy=signal.strategy,
            timeframe=signal.timeframe,
            confluence_score=signal.confidence,
        )
        session.add(trade)
        await session.flush()  # Get the trade ID

        # Generate and save explanation
        explanation_data = explainer.generate_entry_explanation(signal)
        trade_explanation = TradeExplanation(
            trade_id=trade.id,
            reasons=signal.reasons,
            indicators=signal.indicators,
            setup_description=explanation_data["full_text"],
            learning_points=signal.learning_points,
            risk_reward_ratio=signal.risk_reward_ratio,
        )
        session.add(trade_explanation)

        # Save market snapshot
        snapshot = MarketSnapshot(
            trade_id=trade.id,
            pair=signal.pair,
            price=signal.price,
            rsi=signal.indicators.get("rsi"),
            macd=signal.indicators.get("macd"),
            macd_signal=signal.indicators.get("macd_signal"),
            ema_9=signal.indicators.get("ema_9"),
            ema_21=signal.indicators.get("ema_21"),
            ema_50=signal.indicators.get("ema_50"),
            ema_200=signal.indicators.get("ema_200"),
            volume=signal.indicators.get("volume"),
            avg_volume=signal.indicators.get("avg_volume"),
            bb_upper=signal.indicators.get("bb_upper"),
            bb_lower=signal.indicators.get("bb_lower"),
            atr=signal.indicators.get("atr"),
            adx=signal.indicators.get("adx"),
            support_level=signal.indicators.get("support"),
            resistance_level=signal.indicators.get("resistance"),
        )
        session.add(snapshot)

        await session.commit()
        print(f"TRADE OPENED: {signal.action} {signal.pair} @ ${signal.price} | Confidence: {signal.confidence}/5")
        return trade

    async def check_open_trades(self, current_price: float, pair: str, session: AsyncSession):
        """Check if any open trades hit SL/TP."""
        result = await session.execute(
            select(Trade).where(Trade.pair == pair, Trade.status == "OPEN")
        )
        open_trades = result.scalars().all()

        for trade in open_trades:
            should_close = False
            exit_price = current_price

            if trade.side == "BUY":
                if trade.stop_loss and current_price <= trade.stop_loss:
                    should_close = True
                    exit_price = trade.stop_loss
                elif trade.take_profit and current_price >= trade.take_profit:
                    should_close = True
                    exit_price = trade.take_profit
            else:  # SELL
                if trade.stop_loss and current_price >= trade.stop_loss:
                    should_close = True
                    exit_price = trade.stop_loss
                elif trade.take_profit and current_price <= trade.take_profit:
                    should_close = True
                    exit_price = trade.take_profit

            if should_close:
                await self.close_trade(trade, exit_price, session)

    async def close_trade(self, trade: Trade, exit_price: float, session: AsyncSession):
        """Close a trade and calculate PnL."""
        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
            pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity
            pnl_percent = ((trade.entry_price - exit_price) / trade.entry_price) * 100

        trade.exit_price = exit_price
        trade.pnl = round(pnl, 2)
        trade.pnl_percent = round(pnl_percent, 2)
        trade.status = "CLOSED"
        trade.closed_at = datetime.now(timezone.utc)

        # Update portfolio
        portfolio = await self._get_portfolio(session)
        if portfolio:
            portfolio.balance += pnl
            portfolio.total_pnl += pnl
            portfolio.total_trades += 1
            if pnl > 0:
                portfolio.winning_trades += 1
                if pnl > portfolio.best_trade_pnl:
                    portfolio.best_trade_pnl = pnl
            else:
                portfolio.losing_trades += 1
                if pnl < portfolio.worst_trade_pnl:
                    portfolio.worst_trade_pnl = pnl
            portfolio.updated_at = datetime.now(timezone.utc)

        # Generate post-trade analysis
        signal = Signal(
            action=trade.side,
            pair=trade.pair,
            price=trade.entry_price,
            strategy=trade.strategy,
            timeframe=trade.timeframe,
            confidence=trade.confluence_score,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
        )
        analysis_data = explainer.generate_exit_explanation(signal, exit_price, pnl, pnl_percent)

        post_analysis = PostAnalysis(
            trade_id=trade.id,
            result_summary=analysis_data["result_summary"],
            what_went_right=analysis_data["what_went_right"],
            what_went_wrong=analysis_data["what_went_wrong"],
            improvements=analysis_data["improvements"],
            lesson=analysis_data["lesson"],
        )
        session.add(post_analysis)

        await session.commit()
        emoji = "PROFIT" if pnl > 0 else "LOSS"
        print(f"TRADE CLOSED: {trade.pair} | {emoji} ${round(pnl, 2)} ({round(pnl_percent, 2)}%)")

    async def _get_portfolio(self, session: AsyncSession) -> Optional[Portfolio]:
        result = await session.execute(select(Portfolio).limit(1))
        return result.scalars().first()


# Singleton
paper_trader = PaperTrader()
