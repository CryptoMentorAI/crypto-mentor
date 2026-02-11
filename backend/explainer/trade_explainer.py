from backend.strategies.base import Signal


class TradeExplainer:
    """
    Generate human-readable explanations untuk setiap trade.
    Ini 'cikgu' dalam CryptoMentor — explain kenapa bot buat keputusan,
    dan apa yang user boleh belajar.
    """

    def generate_entry_explanation(self, signal: Signal) -> dict:
        """Generate full explanation bila trade dibuka."""

        header = self._format_header(signal)
        reasons_text = self._format_reasons(signal)
        setup_text = self._format_setup(signal)
        strategy_text = self._format_strategy_info(signal)
        learning_text = self._format_learning(signal)
        confluence_text = self._format_confluence(signal)

        full_text = "\n\n".join([
            header, reasons_text, confluence_text, setup_text, strategy_text, learning_text
        ])

        return {
            "full_text": full_text,
            "header": header,
            "reasons": signal.reasons,
            "learning_points": signal.learning_points,
            "setup": {
                "entry": signal.price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "risk_reward": signal.risk_reward_ratio,
            },
            "strategy": signal.strategy,
            "confluence_score": signal.confidence,
            "indicators": signal.indicators,
        }

    def generate_exit_explanation(
        self, signal: Signal, exit_price: float, pnl: float, pnl_percent: float
    ) -> dict:
        """Generate post-trade analysis bila trade ditutup."""

        won = pnl > 0
        hit_tp = (signal.action == "BUY" and exit_price >= signal.take_profit) or \
                 (signal.action == "SELL" and exit_price <= signal.take_profit) \
                 if signal.take_profit else False
        hit_sl = (signal.action == "BUY" and exit_price <= signal.stop_loss) or \
                 (signal.action == "SELL" and exit_price >= signal.stop_loss) \
                 if signal.stop_loss else False

        # Result summary
        emoji = "+" if won else ""
        result = (
            f"TRADE RESULT: {emoji}{round(pnl_percent, 2)}% (${round(pnl, 2)})\n"
            f"{'PROFIT' if won else 'LOSS'} | "
            f"Entry: ${signal.price} → Exit: ${exit_price}"
        )

        # What happened
        what_happened = []
        if hit_tp:
            what_happened.append("Harga hit Take Profit level — trade berjaya ikut plan.")
        elif hit_sl:
            what_happened.append("Harga hit Stop Loss — market bergerak melawan position kita.")
        elif won:
            what_happened.append("Trade ditutup dengan profit sebelum hit TP.")
        else:
            what_happened.append("Trade ditutup dengan loss.")

        # What went right
        what_right = []
        what_wrong = []
        improvements = []

        if won:
            what_right.append("Analysis betul — market bergerak ikut prediction.")
            if hit_tp:
                what_right.append("Take profit level tepat.")
            if signal.confidence >= 4:
                what_right.append("High confluence trade = higher win rate.")
        else:
            what_wrong.append("Market tak bergerak ikut analysis.")
            if hit_sl:
                what_wrong.append(
                    "Stop loss kena hit — tapi ini BUKAN kesilapan. "
                    "Stop loss tu untuk protect modal kau. Tanpa SL, loss boleh jadi lebih besar."
                )
            if signal.confidence <= 2:
                what_wrong.append(
                    "Confluence score rendah — trade macam ni memang higher risk. "
                    "Next time, consider tunggu lebih banyak confirmation."
                )

        # Improvements
        if won and pnl_percent < 1:
            improvements.append(
                "Profit kecil — consider adjust TP atau hold lebih lama bila trend kuat."
            )
        if not won and abs(pnl_percent) > 2:
            improvements.append(
                "Loss agak besar — consider tighten stop loss atau reduce position size."
            )
        if not won:
            improvements.append(
                "Review balik chart — apa yang market 'cakap' yang kita terlepas?"
            )

        # Key lesson
        if won:
            lesson = (
                f"Trade ni berjaya sebab ada {signal.confidence} confluences yang agree. "
                f"LESSON: Patience + confluence = profitable trading. "
                f"Tak perlu trade setiap signal — tunggu yang berkualiti je."
            )
        else:
            lesson = (
                f"Trade ni tak berjaya — dan itu OK. Dalam trading, loss adalah kos belajar. "
                f"Yang penting: (1) Stop loss protect modal kau, "
                f"(2) Satu loss tak bermakna strategy salah — judge over 20-50 trades, "
                f"(3) Review dan improve, jangan give up."
            )

        full_text = (
            f"TRADE RESULT\n{'=' * 40}\n{result}\n\n"
            f"APA YANG JADI:\n" + "\n".join(f"- {w}" for w in what_happened) + "\n\n"
            f"APA YANG BETUL:\n" + "\n".join(f"+ {w}" for w in what_right) + "\n\n" if what_right else ""
            f"APA YANG TAK KENA:\n" + "\n".join(f"- {w}" for w in what_wrong) + "\n\n" if what_wrong else ""
            f"BOLEH IMPROVE:\n" + "\n".join(f"* {i}" for i in improvements) + "\n\n"
            f"LESSON:\n{lesson}"
        )

        return {
            "full_text": full_text,
            "result_summary": result,
            "what_went_right": what_right,
            "what_went_wrong": what_wrong,
            "improvements": improvements,
            "lesson": lesson,
            "won": won,
            "hit_tp": hit_tp,
            "hit_sl": hit_sl,
        }

    # ─── Formatting Helpers ──────────────────

    def _format_header(self, signal: Signal) -> str:
        emoji = "BUY" if signal.action == "BUY" else "SELL"
        return (
            f"{emoji} {signal.pair} @ ${signal.price}\n"
            f"Timeframe: {signal.timeframe} | Confidence: {signal.confidence}/5"
        )

    def _format_reasons(self, signal: Signal) -> str:
        lines = ["KENAPA SAYA " + signal.action + ":"]
        for i, reason in enumerate(signal.reasons, 1):
            lines.append(f"{i}. {reason}")
        return "\n".join(lines)

    def _format_confluence(self, signal: Signal) -> str:
        labels = {1: "Lemah", 2: "Sederhana", 3: "Kuat", 4: "Sangat Kuat", 5: "Extreme"}
        label = labels.get(signal.confidence, "Unknown")
        bar = "█" * signal.confidence + "░" * (5 - signal.confidence)
        return f"CONFLUENCE SCORE: [{bar}] {signal.confidence}/5 ({label})"

    def _format_setup(self, signal: Signal) -> str:
        rr = signal.risk_reward_ratio
        lines = [
            "SETUP:",
            f"  Entry: ${signal.price}",
            f"  Stop Loss: ${signal.stop_loss}" + (
                f" ({'-' if signal.action == 'BUY' else '+'}{round(abs(signal.price - signal.stop_loss) / signal.price * 100, 2)}%)"
                if signal.stop_loss else ""
            ),
            f"  Take Profit: ${signal.take_profit}" + (
                f" ({'+' if signal.action == 'BUY' else '-'}{round(abs(signal.take_profit - signal.price) / signal.price * 100, 2)}%)"
                if signal.take_profit else ""
            ),
        ]
        if rr:
            lines.append(f"  Risk:Reward = 1:{rr}")
        return "\n".join(lines)

    def _format_strategy_info(self, signal: Signal) -> str:
        return f"STRATEGY: {signal.strategy}"

    def _format_learning(self, signal: Signal) -> str:
        if not signal.learning_points:
            return ""
        lines = ["APA KAU BOLEH BELAJAR:"]
        for point in signal.learning_points:
            lines.append(f"  - {point}")
        return "\n".join(lines)


# Singleton
explainer = TradeExplainer()
