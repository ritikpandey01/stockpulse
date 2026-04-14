import logging
import yfinance as yf
import pandas as pd
from services.market_data import fetch_stock_data

logger = logging.getLogger(__name__)

# Major indices
INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
}

SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Disc.": "XLY",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Comm. Services": "XLC",
    "Consumer Staples": "XLP",
}


def get_indices_data() -> list:
    """Fetch current data for major market indices."""
    results = []
    for name, symbol in INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 2:
                continue
            current = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2])
            change = ((current - prev) / prev) * 100
            results.append({
                "name": name,
                "symbol": symbol,
                "value": round(current, 2),
                "change": round(change, 2),
            })
        except Exception as e:
            logger.warning(f"Index fetch error for {name}: {e}")
    return results


def get_sector_heatmap() -> list:
    """Get sector performance data for heatmap visualization."""
    sectors = []
    for name, etf in SECTOR_ETFS.items():
        try:
            data = fetch_stock_data(etf, period="5d", interval="1d")
            if data is None or len(data) < 2:
                continue

            change_1d = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100

            # Weekly change
            change_5d = 0
            if len(data) >= 5:
                change_5d = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100

            sectors.append({
                "sector": name,
                "etf": etf,
                "change_1d": round(float(change_1d), 2),
                "change_5d": round(float(change_5d), 2),
                "price": round(float(data['Close'].iloc[-1]), 2),
            })
        except Exception as e:
            logger.warning(f"Sector error for {name}: {e}")

    sectors.sort(key=lambda x: x['change_1d'], reverse=True)
    return sectors


def calculate_fear_greed() -> dict:
    """Calculate a simplified fear/greed composite score."""
    score = 50  # neutral baseline
    factors = []

    try:
        # VIX component (fear indicator)
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="1mo")
        if not vix_hist.empty:
            vix_current = float(vix_hist['Close'].iloc[-1])
            vix_avg = float(vix_hist['Close'].mean())
            if vix_current > 30:
                score -= 20
                factors.append(f"High VIX ({vix_current:.1f}) — Extreme fear")
            elif vix_current > 20:
                score -= 10
                factors.append(f"Elevated VIX ({vix_current:.1f}) — Moderate fear")
            elif vix_current < 15:
                score += 15
                factors.append(f"Low VIX ({vix_current:.1f}) — Complacency/Greed")
            else:
                factors.append(f"Normal VIX ({vix_current:.1f})")

        # S&P 500 momentum
        sp = yf.Ticker("^GSPC")
        sp_hist = sp.history(period="1mo")
        if not sp_hist.empty and len(sp_hist) >= 20:
            sp_return = (sp_hist['Close'].iloc[-1] - sp_hist['Close'].iloc[0]) / sp_hist['Close'].iloc[0] * 100
            if sp_return > 5:
                score += 15
                factors.append(f"S&P 500 up {sp_return:.1f}% this month — Strong momentum")
            elif sp_return > 0:
                score += 5
                factors.append(f"S&P 500 up {sp_return:.1f}% this month — Positive")
            elif sp_return > -5:
                score -= 5
                factors.append(f"S&P 500 down {abs(sp_return):.1f}% this month — Mildly bearish")
            else:
                score -= 15
                factors.append(f"S&P 500 down {abs(sp_return):.1f}% this month — Strong selling")

        # Market breadth (using advance/decline proxy via sector ETFs)
        advancing = sum(1 for s in get_sector_heatmap() if s['change_1d'] > 0)
        total_sectors = len(SECTOR_ETFS)
        breadth = advancing / total_sectors if total_sectors > 0 else 0.5
        if breadth > 0.7:
            score += 10
            factors.append(f"{advancing}/{total_sectors} sectors advancing — Broad strength")
        elif breadth < 0.3:
            score -= 10
            factors.append(f"Only {advancing}/{total_sectors} sectors advancing — Narrow market")

    except Exception as e:
        logger.warning(f"Fear/greed calc error: {e}")
        factors.append("Partial data available")

    score = max(0, min(100, score))

    if score >= 75:
        label = "Extreme Greed"
    elif score >= 55:
        label = "Greed"
    elif score >= 45:
        label = "Neutral"
    elif score >= 25:
        label = "Fear"
    else:
        label = "Extreme Fear"

    return {
        "score": score,
        "label": label,
        "factors": factors,
    }


def get_market_overview() -> dict:
    """Full market overview combining all data."""
    return {
        "indices": get_indices_data(),
        "sectors": get_sector_heatmap(),
        "fear_greed": calculate_fear_greed(),
    }
