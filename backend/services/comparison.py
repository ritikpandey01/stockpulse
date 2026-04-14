import logging
import numpy as np
import pandas as pd
from services.market_data import fetch_stock_data, get_stock_info
from services.technical import calculate_features, generate_signals, get_performance_metrics

logger = logging.getLogger(__name__)


def compare_stocks(symbols: list[str], period: str = "3mo", interval: str = "1d") -> dict:
    """Compare multiple stocks with normalized returns and key metrics."""
    if not symbols or len(symbols) < 2:
        return {"error": "Need at least 2 symbols to compare"}

    symbols = [s.upper().strip() for s in symbols[:5]]  # Max 5

    stock_data = {}
    comparison_table = []
    normalized_series = {}

    for symbol in symbols:
        try:
            data = fetch_stock_data(symbol, period=period, interval=interval)
            if data is None or len(data) < 5:
                continue

            stock_data[symbol] = data
            info = get_stock_info(symbol)
            featured = calculate_features(data)
            signals = generate_signals(featured)
            perf = get_performance_metrics(featured)

            current_price = float(data['Close'].iloc[-1])
            start_price = float(data['Close'].iloc[0])
            total_return = ((current_price - start_price) / start_price) * 100

            comparison_table.append({
                "symbol": symbol,
                "name": info.get("name", symbol),
                "sector": info.get("sector", "N/A"),
                "price": round(current_price, 2),
                "total_return": round(total_return, 2),
                "signal": signals['overall'],
                "rsi": signals['rsi']['value'],
                "macd": signals['macd'],
                "volatility": perf['volatility'],
                "sharpe": perf['sharpe_ratio'],
                "max_drawdown": perf['max_drawdown'],
                "pe_ratio": info.get("pe_ratio"),
                "market_cap": info.get("market_cap", 0),
            })

            # Normalized price (base 100)
            base = float(data['Close'].iloc[0])
            norm = []
            for _, row in data.iterrows():
                norm.append({
                    "time": int(row['Date'].timestamp()),
                    "value": round(float(row['Close']) / base * 100, 2),
                })
            normalized_series[symbol] = norm

        except Exception as e:
            logger.warning(f"Compare error for {symbol}: {e}")
            continue

    # Correlation matrix
    correlation = {}
    valid_symbols = list(stock_data.keys())
    if len(valid_symbols) >= 2:
        returns_df = pd.DataFrame()
        for sym in valid_symbols:
            returns_df[sym] = stock_data[sym]['Close'].pct_change().dropna().reset_index(drop=True)

        # Align lengths
        min_len = returns_df.dropna().shape[0]
        if min_len > 5:
            corr_matrix = returns_df.dropna().corr()
            for s1 in valid_symbols:
                correlation[s1] = {}
                for s2 in valid_symbols:
                    try:
                        correlation[s1][s2] = round(float(corr_matrix.loc[s1, s2]), 3)
                    except Exception:
                        correlation[s1][s2] = None

    # Sort comparison by total return
    comparison_table.sort(key=lambda x: x['total_return'], reverse=True)

    return {
        "symbols": valid_symbols,
        "comparison": comparison_table,
        "normalized_series": normalized_series,
        "correlation": correlation,
        "period": period,
    }
