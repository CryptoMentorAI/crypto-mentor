import asyncio
from typing import Optional

from backend.core.config import settings
from backend.core.market_data import market_data
from backend.core.trader import paper_trader
from backend.strategies.orchestrator import orchestrator
from backend.database.db import async_session


class TradingBot:
    """
    Main bot loop — fetch data, analyze, trade, repeat.
    """

    def __init__(self):
        self.running = False
        self.pair = settings.DEFAULT_PAIR
        self.timeframe = settings.DEFAULT_TIMEFRAME
        self.scan_interval = 60  # Check every 60 seconds
        self._ws_callbacks: list = []

    def add_ws_callback(self, callback):
        """Register WebSocket callback for real-time updates to frontend."""
        self._ws_callbacks.append(callback)

    def remove_ws_callback(self, callback):
        if callback in self._ws_callbacks:
            self._ws_callbacks.remove(callback)

    async def _broadcast(self, event: str, data: dict):
        for cb in self._ws_callbacks:
            try:
                await cb(event, data)
            except Exception:
                pass

    async def run(self):
        """Main bot loop."""
        self.running = True
        print(f"Bot started | Pair: {self.pair} | Timeframe: {self.timeframe}")

        await market_data.initialize()

        # Start real-time price stream (OKX WebSocket → frontend)
        async def _on_tick(pair, price, timestamp):
            await self._broadcast("tick_update", {
                "pair": pair,
                "price": price,
                "timestamp": timestamp,
            })

        market_data.add_price_listener(_on_tick)
        self._stream_task = asyncio.create_task(
            market_data.start_realtime_stream(self.pair)
        )

        cycle = 0
        while self.running:
            try:
                cycle += 1
                print(f"\n--- Scan #{cycle} ---")

                # 1. Fetch market data
                df = await market_data.get_candles(self.pair, self.timeframe)
                indicators = await market_data.get_indicators(self.pair, self.timeframe)
                current_price = indicators["price"]

                # Broadcast price update
                await self._broadcast("price_update", {
                    "pair": self.pair,
                    "price": current_price,
                    "indicators": indicators,
                })

                async with async_session() as session:
                    # 2. Check open trades for SL/TP
                    await paper_trader.check_open_trades(current_price, self.pair, session)

                    # 3. Analyze all strategies
                    signal = await orchestrator.analyze_all(
                        df, indicators, self.pair, self.timeframe
                    )

                    if signal:
                        print(f"Signal: {signal.action} {signal.pair} @ ${signal.price} | Confidence: {signal.confidence}/5")

                        # 4. Execute trade
                        trade = await paper_trader.execute_trade(signal, session)

                        if trade:
                            # Broadcast new trade
                            await self._broadcast("new_trade", {
                                "id": trade.id,
                                "pair": trade.pair,
                                "side": trade.side,
                                "entry_price": trade.entry_price,
                                "stop_loss": trade.stop_loss,
                                "take_profit": trade.take_profit,
                                "strategy": trade.strategy,
                                "confluence_score": trade.confluence_score,
                            })
                    else:
                        print(f"No signal | {self.pair} @ ${current_price}")

            except Exception as e:
                print(f"Bot error: {e}")

            await asyncio.sleep(self.scan_interval)

    async def stop(self):
        self.running = False
        if hasattr(self, "_stream_task"):
            self._stream_task.cancel()
        await market_data.close()


# Singleton
trading_bot = TradingBot()
