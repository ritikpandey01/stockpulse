import logging
import yfinance as yf
from services.market_data import fetch_stock_data
from services.technical import calculate_features, generate_signals

logger = logging.getLogger(__name__)

# Extended watchlist for screener
SCREENER_UNIVERSE = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC", "CRM",
    "NFLX", "ADBE", "ORCL", "CSCO", "AVGO", "QCOM", "TXN", "SHOP", "SQ", "PLTR",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "C", "BLK",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "LLY", "AMGN", "BMY",
    # Consumer
    "WMT", "COST", "HD", "NKE", "SBUX", "MCD", "TGT", "LOW", "DIS", "ABNB",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG",
    # Industrial
    "BA", "CAT", "GE", "HON", "UPS",
    # Other
    "COIN", "SOFI", "SNAP", "PYPL", "UBER",
]


def screen_stocks(
    sector: str = None,
    min_price: float = None,
    max_price: float = None,
    min_market_cap: float = None,
    min_pe: float = None,
    max_pe: float = None,
    min_rsi: float = None,
    max_rsi: float = None,
    signal_filter: str = None,
    sort_by: str = "score",
    limit: int = 20,
) -> list:
    """Screen stocks from the universe based on filters."""
    results = []

    for symbol in SCREENER_UNIVERSE:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            stock_sector = info.get("sector", "N/A")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            market_cap = info.get("marketCap", 0)
            pe = info.get("trailingPE")

            if price is None:
                continue

            # Apply filters
            if sector and sector.lower() not in stock_sector.lower():
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            if min_market_cap is not None and (market_cap or 0) < min_market_cap:
                continue
            if min_pe is not None and (pe is None or pe < min_pe):
                continue
            if max_pe is not None and (pe is None or pe > max_pe):
                continue

            # Get technical data for RSI/signals
            data = fetch_stock_data(symbol, period="1mo", interval="1d")
            rsi_value = None
            signal = "N/A"
            score = 50

            if data is not None and len(data) >= 15:
                featured = calculate_features(data)
                signals = generate_signals(featured)
                rsi_value = signals['rsi']['value']
                signal = signals['overall']

                # Momentum score
                raw_score = signals['score']
                score = (raw_score + 4) / 8 * 100

                # RSI filter
                if min_rsi is not None and (rsi_value is None or rsi_value < min_rsi):
                    continue
                if max_rsi is not None and (rsi_value is None or rsi_value > max_rsi):
                    continue

                # Signal filter
                if signal_filter and signal_filter.lower() not in signal.lower():
                    continue

            # 5-day return
            ret_5d = 0
            if data is not None and len(data) >= 5:
                ret_5d = ((data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5]) * 100

            results.append({
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "sector": stock_sector,
                "price": round(float(price), 2),
                "market_cap": market_cap,
                "pe_ratio": round(float(pe), 2) if pe else None,
                "rsi": round(rsi_value, 1) if rsi_value else None,
                "signal": signal,
                "score": round(score, 1),
                "return_5d": round(float(ret_5d), 2),
                "dividend_yield": round(float(info.get("dividendYield", 0) or 0) * 100, 2),
            })

        except Exception as e:
            logger.warning(f"Screener skip {symbol}: {e}")
            continue

    # Sort
    sort_key = sort_by if sort_by in ["score", "price", "market_cap", "pe_ratio", "rsi", "return_5d"] else "score"
    results.sort(key=lambda x: x.get(sort_key) or 0, reverse=(sort_key != "pe_ratio"))

    return results[:limit]
