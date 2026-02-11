"""
Trading Concepts Glossary — Educational reference untuk user.
Setiap concept ada explanation dalam Bahasa Melayu yang mudah faham.
"""

CONCEPTS = {
    "rsi": {
        "name": "RSI (Relative Strength Index)",
        "short": "Ukur momentum — adakah harga dah naik/turun terlalu banyak",
        "explanation": (
            "RSI adalah indicator yang ukur kelajuan dan magnitude pergerakan harga. "
            "Nilainya antara 0-100.\n\n"
            "- RSI < 30 = OVERSOLD → Harga dah jatuh banyak, mungkin nak bounce naik\n"
            "- RSI > 70 = OVERBOUGHT → Harga dah naik banyak, mungkin nak pullback turun\n"
            "- RSI = 50 = Neutral\n\n"
            "Analogi: Macam rubber band. Kalau stretch terlalu banyak (RSI extreme), "
            "ia akan snap balik ke tengah.\n\n"
            "TIPS:\n"
            "- RSI bukan signal beli/jual sendiri — guna sebagai confirmation\n"
            "- Dalam strong uptrend, RSI boleh stay > 70 lama\n"
            "- RSI divergence (harga naik tapi RSI turun) = warning signal kuat"
        ),
        "formula": "RSI = 100 - (100 / (1 + RS)), dimana RS = Average Gain / Average Loss",
    },
    "macd": {
        "name": "MACD (Moving Average Convergence Divergence)",
        "short": "Detect perubahan momentum dan arah trend",
        "explanation": (
            "MACD tunjuk hubungan antara 2 moving averages. "
            "Ia ada 3 komponen:\n\n"
            "1. MACD Line = EMA(12) - EMA(26)\n"
            "2. Signal Line = EMA(9) of MACD Line\n"
            "3. Histogram = MACD Line - Signal Line\n\n"
            "Signal:\n"
            "- MACD cross ATAS signal line = BULLISH (momentum naik)\n"
            "- MACD cross BAWAH signal line = BEARISH (momentum turun)\n"
            "- Histogram makin besar = momentum makin kuat\n\n"
            "Analogi: Macam kereta. MACD tunjuk adakah kereta sedang pecut (accelerate) "
            "atau brake. Histogram = berapa kuat kau pijak minyak/brake."
        ),
        "formula": "MACD = EMA(12) - EMA(26), Signal = EMA(9) of MACD",
    },
    "ema": {
        "name": "EMA (Exponential Moving Average)",
        "short": "Purata harga yang bagi lebih weight pada data terbaru",
        "explanation": (
            "EMA adalah moving average yang lebih responsive pada pergerakan harga terkini "
            "berbanding SMA (Simple Moving Average).\n\n"
            "Common EMAs:\n"
            "- EMA 9 = Sangat short-term (scalping)\n"
            "- EMA 21 = Short-term trend\n"
            "- EMA 50 = Medium-term trend\n"
            "- EMA 200 = Long-term trend (institutional level)\n\n"
            "Signal:\n"
            "- Harga ATAS EMA = Bullish trend\n"
            "- Harga BAWAH EMA = Bearish trend\n"
            "- EMA cepat cross EMA lambat ke atas = Golden Cross (bullish)\n"
            "- EMA cepat cross EMA lambat ke bawah = Death Cross (bearish)\n\n"
            "Analogi: EMA macam GPS yang tunjuk arah trend. "
            "EMA 200 = highway direction (big picture), EMA 9 = jalan kampung (short-term)."
        ),
        "formula": "EMA = Price × k + Previous EMA × (1-k), dimana k = 2/(period+1)",
    },
    "bollinger_bands": {
        "name": "Bollinger Bands",
        "short": "Ukur volatility dan detect harga extreme",
        "explanation": (
            "Bollinger Bands terdiri daripada 3 lines:\n"
            "1. Middle Band = SMA(20)\n"
            "2. Upper Band = SMA(20) + 2×Standard Deviation\n"
            "3. Lower Band = SMA(20) - 2×Standard Deviation\n\n"
            "95% masa, harga akan stay dalam bands. Kalau keluar = extreme move.\n\n"
            "Signal:\n"
            "- Harga touch lower band = potential buy (oversold)\n"
            "- Harga touch upper band = potential sell (overbought)\n"
            "- Bands squeeze (sempit) = volatility rendah, breakout coming!\n"
            "- Bands expand (lebar) = volatility tinggi\n\n"
            "Analogi: Macam highway. Middle band = center line. "
            "Upper & lower bands = guardrails. Harga biasanya stay dalam guardrails, "
            "kalau langgar = something big happening."
        ),
        "formula": "Upper = SMA(20) + 2σ, Lower = SMA(20) - 2σ",
    },
    "support_resistance": {
        "name": "Support & Resistance",
        "short": "Level harga dimana buyer/seller selalu masuk",
        "explanation": (
            "Support = lantai harga. Level dimana harga selalu bounce naik sebab "
            "buyer masuk (demand zone).\n\n"
            "Resistance = siling harga. Level dimana harga selalu reject turun sebab "
            "seller masuk (supply zone).\n\n"
            "Kenapa S/R penting:\n"
            "- Ramai trader tengok level yang sama → self-fulfilling prophecy\n"
            "- Lagi banyak kali harga test tanpa break = lagi kuat level tu\n"
            "- Bila support break → jadi resistance baru (dan sebaliknya)\n\n"
            "TIPS:\n"
            "- S/R bukan exact price — ia ZONE (kawasan)\n"
            "- Combine S/R dengan indicator lain untuk confirmation\n"
            "- Jangan buy TEPAT di support — tunggu confirmation candle"
        ),
        "formula": "Manual identification based on price history",
    },
    "candlestick_patterns": {
        "name": "Candlestick Patterns",
        "short": "Pattern dari candle yang predict pergerakan seterusnya",
        "explanation": (
            "Setiap candle ceritakan CERITA tentang pertarungan buyer vs seller:\n\n"
            "BULLISH PATTERNS (signal naik):\n"
            "- Hammer: Ekor bawah panjang, body kecil atas → seller gagal push turun\n"
            "- Bullish Engulfing: Candle hijau besar telan candle merah → buyer ambil alih\n"
            "- Morning Star: 3 candle pattern — merah, doji, hijau → reversal naik\n\n"
            "BEARISH PATTERNS (signal turun):\n"
            "- Shooting Star: Ekor atas panjang, body kecil bawah → buyer gagal push naik\n"
            "- Bearish Engulfing: Candle merah besar telan candle hijau → seller ambil alih\n"
            "- Evening Star: Hijau, doji, merah → reversal turun\n\n"
            "NEUTRAL:\n"
            "- Doji: Body sangat kecil → market tak pasti, tunggu confirmation\n\n"
            "TIPS: Pattern paling bermakna dekat S/R level. "
            "Hammer dekat support = VERY bullish. Shooting star dekat resistance = VERY bearish."
        ),
        "formula": "Visual pattern recognition",
    },
    "adx": {
        "name": "ADX (Average Directional Index)",
        "short": "Ukur KEKUATAN trend (bukan arah)",
        "explanation": (
            "ADX ukur kekuatan trend, BUKAN arah. Nilainya 0-100:\n\n"
            "- ADX < 20 = Tiada trend (market sideways/choppy)\n"
            "- ADX 20-40 = Trend sederhana\n"
            "- ADX 40-60 = Trend kuat\n"
            "- ADX > 60 = Trend sangat kuat (rare)\n\n"
            "Guna ADX untuk:\n"
            "- Decide guna strategy apa: ADX tinggi = trend following, ADX rendah = mean reversion\n"
            "- Filter false signals: Kalau ADX rendah, banyak signal akan jadi palsu\n"
            "- Detect trend exhaustion: ADX mula turun = trend mungkin nak habis\n\n"
            "Analogi: ADX macam speedometer trend. Tak tunjuk arah, tapi tunjuk laju."
        ),
        "formula": "ADX = SMA(DX, 14), dimana DX = |+DI - -DI| / |+DI + -DI| × 100",
    },
    "risk_reward": {
        "name": "Risk:Reward Ratio",
        "short": "Berapa banyak kau boleh untung vs berapa banyak kau boleh rugi",
        "explanation": (
            "Risk:Reward ratio compare potential loss vs potential profit:\n\n"
            "Contoh: Buy BTC at $67,000\n"
            "- Stop Loss: $66,500 (risk = $500)\n"
            "- Take Profit: $68,000 (reward = $1,000)\n"
            "- R:R = 1:2 (risk $1 untuk potential $2)\n\n"
            "GOLDEN RULE:\n"
            "- Minimum R:R = 1:1.5 (lebih baik 1:2 atau 1:3)\n"
            "- Dengan R:R 1:2, kau boleh salah 60% masa dan MASIH untung!\n"
            "  (40 wins × $2 = $80, 60 losses × $1 = $60, NET = +$20)\n\n"
            "TIPS:\n"
            "- SELALU set R:R sebelum masuk trade\n"
            "- Jangan adjust stop loss ke arah yang lebih rugi\n"
            "- R:R yang baik + win rate 40-50% = profitable trader"
        ),
        "formula": "R:R = (Take Profit - Entry) / (Entry - Stop Loss)",
    },
    "volume": {
        "name": "Volume",
        "short": "Berapa banyak aset yang di-trade — tenaga di sebalik harga",
        "explanation": (
            "Volume = jumlah unit yang diperdagangkan dalam satu tempoh.\n\n"
            "Kenapa volume penting:\n"
            "- Volume CONFIRM pergerakan harga\n"
            "- Harga naik + volume tinggi = STRONG rally (ramai orang beli)\n"
            "- Harga naik + volume rendah = WEAK rally (tak ramai yang percaya)\n"
            "- Breakout + volume tinggi = REAL breakout\n"
            "- Breakout + volume rendah = likely FAKE breakout\n\n"
            "Analogi: Volume macam tenaga di sebalik pukulan. "
            "Harga = arah pukulan, Volume = kekuatan pukulan. "
            "Pukulan lemah tak boleh tembus pertahanan (resistance)."
        ),
        "formula": "Volume = total units traded in period",
    },
}


def get_concept(name: str) -> dict | None:
    """Get a trading concept explanation."""
    return CONCEPTS.get(name.lower())


def get_all_concepts() -> dict:
    """Get all trading concepts."""
    return CONCEPTS


def search_concepts(query: str) -> list[dict]:
    """Search concepts by name or keyword."""
    query = query.lower()
    results = []
    for key, concept in CONCEPTS.items():
        if (
            query in key
            or query in concept["name"].lower()
            or query in concept["short"].lower()
        ):
            results.append({"key": key, **concept})
    return results
