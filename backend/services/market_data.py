import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame | None:
    """Fetch OHLCV data from Yahoo Finance."""
    try:
        logger.info(f"Fetching data for {symbol} | period={period} interval={interval}")
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        if data.empty:
            return None
        data.columns = ['_'.join(col).strip() for col in data.columns.to_flat_index()]
        data.reset_index(inplace=True)
        data.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        if len(data) < 2:
            return None
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None


def get_current_price(symbol: str) -> float | None:
    """Get the most recent price for a stock symbol."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            hist = ticker.history(period="5d")
        if hist.empty:
            return None
        return float(hist['Close'].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching current price for {symbol}: {e}")
        return None


def get_stock_info(symbol: str) -> dict:
    """Get basic stock info (name, sector, etc.)."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "name": info.get("shortName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "dividend_yield": info.get("dividendYield", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
        }
    except Exception:
        return {"name": symbol, "sector": "N/A", "industry": "N/A"}
