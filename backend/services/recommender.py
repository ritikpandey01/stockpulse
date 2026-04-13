import logging
import pandas as pd
from services.market_data import fetch_stock_data, get_current_price, get_stock_info
from services.technical import calculate_features, generate_signals

logger = logging.getLogger(__name__)

# Curated watchlist of popular liquid stocks across sectors
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "JPM", "V", "WMT", "JNJ", "PG", "UNH",
    "HD", "MA", "XOM", "ABBV", "COST", "CRM", "NFLX",
    "AMD", "INTC", "DIS", "PYPL", "BA", "NKE", "SNAP",
    "COIN", "PLTR", "SOFI",
]


def score_stock(symbol: str) -> dict | None:
    """Quick-score a single stock based on technical signals."""
    try:
        data = fetch_stock_data(symbol, period="1mo", interval="1d")
        if data is None or len(data) < 15:
            return None

        featured = calculate_features(data)
        signals = generate_signals(featured)
        current_price = float(featured['Close'].iloc[-1])

        # Momentum score (-4 to +4 from signals, normalize to 0-100)
        raw_score = signals['score']
        momentum_score = (raw_score + 4) / 8 * 100

        # Trend: price vs ma_20
        ma20 = featured['ma_20'].iloc[-1]
        trend_bullish = current_price > ma20 if pd.notna(ma20) else True

        # Recent performance (5 day return)
        ret_5d = ((featured['Close'].iloc[-1] - featured['Close'].iloc[-5]) / featured['Close'].iloc[-5] * 100) if len(featured) >= 5 else 0

        composite = momentum_score * 0.6 + (50 + ret_5d * 5) * 0.4
        composite = max(0, min(100, composite))

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "signal": signals['overall'],
            "score": round(composite, 1),
            "rsi": signals['rsi']['value'],
            "macd": signals['macd'],
            "trend": "Uptrend" if trend_bullish else "Downtrend",
            "return_5d": round(float(ret_5d), 2),
        }
    except Exception as e:
        logger.warning(f"Score error for {symbol}: {e}")
        return None


def get_top_recommendations(limit: int = 5) -> list[dict]:
    """Scan watchlist and return top picks sorted by composite score."""
    results = []
    for symbol in WATCHLIST:
        scored = score_stock(symbol)
        if scored:
            results.append(scored)

    # Sort by composite score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def get_sector_movers() -> list[dict]:
    """Quick sector analysis using representative ETFs."""
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financial": "XLF",
        "Energy": "XLE",
        "Consumer": "XLY",
        "Industrial": "XLI",
    }

    movers = []
    for sector, etf in sector_etfs.items():
        try:
            data = fetch_stock_data(etf, period="5d", interval="1d")
            if data is not None and len(data) >= 2:
                change = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
                movers.append({
                    "sector": sector,
                    "etf": etf,
                    "change": round(float(change), 2),
                })
        except Exception:
            pass

    movers.sort(key=lambda x: x['change'], reverse=True)
    return movers
