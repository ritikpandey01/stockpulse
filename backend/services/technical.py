import pandas as pd
import numpy as np
import ta  # type: ignore
import logging

logger = logging.getLogger(__name__)


def calculate_features(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators on OHLCV data. Ported from risk/tech.py."""
    try:
        df = data.copy()

        # Lag features
        df['Lag1'] = df['Close'].shift(1)
        df['Lag2'] = df['Close'].shift(2)
        df['prev_high'] = df['High'].shift(1)
        df['prev_low'] = df['Low'].shift(1)
        df['prev_open'] = df['Open'].shift(1)
        df['prev_vol'] = df['Volume'].shift(1)

        # Moving Averages
        df['ma_5'] = df['Close'].rolling(5).mean()
        df['ma_10'] = df['Close'].rolling(10).mean()
        df['ma_20'] = df['Close'].rolling(20).mean()
        df['ma_50'] = df['Close'].rolling(50).mean()
        df['ema_9'] = ta.trend.ema_indicator(df['Close'], 9)

        # Momentum
        df['RSI'] = ta.momentum.rsi(df['Close'])
        df['MACD'] = ta.trend.macd_diff(df['Close'])
        df['MFI'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'])

        # Volatility
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])

        # Volume
        df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()

        # Support / Resistance
        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = 2 * df['Pivot'] - df['Low']
        df['S1'] = 2 * df['Pivot'] - df['High']

        return df
    except Exception as e:
        logger.error(f"Feature calculation error: {e}")
        raise


def generate_signals(df: pd.DataFrame) -> dict:
    """Generate trading signals from featured data. Returns JSON-safe dict."""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    macd_signal = "Bullish" if latest['MACD'] > 0 else "Bearish"
    rsi_val = float(latest['RSI']) if pd.notna(latest['RSI']) else 50.0
    rsi_signal = "Oversold" if rsi_val < 30 else "Overbought" if rsi_val > 70 else "Neutral"

    bb_signal = "Oversold"
    if pd.notna(latest['BB_lower']) and pd.notna(latest['BB_upper']):
        if latest['Close'] > latest['BB_upper']:
            bb_signal = "Overbought"
        elif latest['Close'] < latest['BB_lower']:
            bb_signal = "Oversold"
        else:
            bb_signal = "Neutral"

    vol_sma = latest.get('Volume_SMA', None)
    volume_signal = "Above Average" if (vol_sma and pd.notna(vol_sma) and latest['Volume'] > vol_sma * 1.5) else "Below Average"

    # Combined strength: -4 to +4
    score = 0
    score += 1 if macd_signal == "Bullish" else -1
    score += 1 if rsi_signal == "Oversold" else (-1 if rsi_signal == "Overbought" else 0)
    score += 1 if bb_signal == "Oversold" else (-1 if bb_signal == "Overbought" else 0)
    score += 1 if volume_signal == "Above Average" else 0

    if score >= 2:
        overall = "Strong Buy"
    elif score > 0:
        overall = "Buy"
    elif score <= -2:
        overall = "Strong Sell"
    elif score < 0:
        overall = "Sell"
    else:
        overall = "Neutral"

    return {
        "overall": overall,
        "score": score,
        "macd": macd_signal,
        "rsi": {"value": round(rsi_val, 2), "signal": rsi_signal},
        "bollinger": bb_signal,
        "volume": volume_signal,
        "mfi": round(float(latest['MFI']), 2) if pd.notna(latest.get('MFI')) else None,
    }


def expert_risk_assessment(df: pd.DataFrame) -> dict:
    """Rule-based expert risk system. Ported from risk/tech.py expert_risk_system()."""
    if df.empty:
        return {"score": 50, "class": "MEDIUM", "factors": ["Insufficient data"]}

    latest = df.iloc[-1]
    risk_score = 0
    factors = []

    # RSI
    rsi = float(latest['RSI']) if pd.notna(latest.get('RSI')) else 50
    if rsi > 70:
        c = min(25, (rsi - 70) * 1.25)
        risk_score += c
        factors.append(f"RSI Overbought at {rsi:.1f} — potential correction (+{c:.0f} pts)")
    elif rsi < 30:
        risk_score -= 15
        factors.append(f"RSI Oversold at {rsi:.1f} — limited downside (-15 pts)")
    else:
        factors.append(f"RSI Neutral at {rsi:.1f}")

    # MACD
    macd = float(latest['MACD']) if pd.notna(latest.get('MACD')) else 0
    ma20 = float(latest.get('ma_20', 0)) if pd.notna(latest.get('ma_20')) else 0
    if macd < 0 and latest['Close'] > ma20:
        risk_score += 20
        factors.append(f"Bearish MACD divergence ({macd:.2f}) while price above 20-MA (+20 pts)")
    elif macd > 0:
        factors.append(f"Bullish MACD ({macd:.2f})")
    else:
        factors.append(f"Bearish MACD ({macd:.2f})")

    # Volume
    vol_sma = latest.get('Volume_SMA')
    if vol_sma and pd.notna(vol_sma) and vol_sma > 0:
        if latest['Volume'] > vol_sma * 1.8:
            if latest['Close'] < latest['Open']:
                risk_score += 30
                factors.append(f"High volume selling — {latest['Volume']/vol_sma:.1f}x avg volume (+30 pts)")
            else:
                factors.append("High volume buying — bullish")

    # Bollinger
    if pd.notna(latest.get('BB_upper')) and latest['Close'] > latest['BB_upper']:
        risk_score += 15
        factors.append(f"Price above upper Bollinger Band — overextended (+15 pts)")
    elif pd.notna(latest.get('BB_lower')) and latest['Close'] < latest['BB_lower']:
        risk_score -= 10
        factors.append("Price below lower Bollinger Band — potential reversal (-10 pts)")

    # Support / Resistance
    if pd.notna(latest.get('R1')) and latest['Close'] > latest['R1'] * 0.98:
        risk_score += 20
        factors.append(f"Near resistance ${latest['R1']:.2f} (+20 pts)")
    elif pd.notna(latest.get('S1')) and latest['Close'] < latest['S1'] * 1.02:
        factors.append(f"Near support ${latest['S1']:.2f} — provides protection")

    # ATR
    if pd.notna(latest.get('ATR')) and latest['Close'] > 0:
        atr_pct = (latest['ATR'] / latest['Close']) * 100
        if atr_pct > 3:
            risk_score += 10
            factors.append(f"High volatility — ATR {atr_pct:.1f}% of price (+10 pts)")

    # Normalize
    risk_score = max(0, min(100, risk_score + 50))

    if risk_score > 60:
        risk_class = "HIGH"
    elif risk_score > 30:
        risk_class = "MEDIUM"
    else:
        risk_class = "LOW"

    return {"score": round(risk_score, 1), "class": risk_class, "factors": factors}


def get_performance_metrics(df: pd.DataFrame) -> dict:
    """Calculate statistical performance metrics."""
    returns = df['Close'].pct_change().dropna()
    volatility = float(returns.std() * np.sqrt(252))
    sharpe = float((returns.mean() * 252) / (returns.std() * np.sqrt(252))) if returns.std() > 0 else 0
    max_dd = float((df['Close'] / df['Close'].cummax() - 1).min())

    return {
        "volatility": round(volatility * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_dd * 100, 2),
    }


def get_returns_distribution(df: pd.DataFrame) -> dict:
    """Calculate returns distribution data for histogram chart."""
    returns = df['Close'].pct_change().dropna() * 100  # percentage
    if len(returns) < 5:
        return {"bins": [], "counts": [], "mean": 0, "std": 0}

    counts, bin_edges = np.histogram(returns, bins=30)
    bins = [(round(float(bin_edges[i]), 3), round(float(bin_edges[i + 1]), 3)) for i in range(len(counts))]

    return {
        "bins": bins,
        "counts": [int(c) for c in counts],
        "mean": round(float(returns.mean()), 4),
        "std": round(float(returns.std()), 4),
        "skewness": round(float(returns.skew()), 4),
        "kurtosis": round(float(returns.kurtosis()), 4),
        "min": round(float(returns.min()), 4),
        "max": round(float(returns.max()), 4),
    }


def get_descriptive_stats(df: pd.DataFrame) -> dict:
    """Calculate descriptive statistics for the stock data."""
    close = df['Close']
    volume = df['Volume']
    returns = close.pct_change().dropna()

    return {
        "price": {
            "current": round(float(close.iloc[-1]), 2),
            "mean": round(float(close.mean()), 2),
            "median": round(float(close.median()), 2),
            "std": round(float(close.std()), 2),
            "min": round(float(close.min()), 2),
            "max": round(float(close.max()), 2),
            "range": round(float(close.max() - close.min()), 2),
        },
        "returns": {
            "mean_daily": round(float(returns.mean() * 100), 4),
            "std_daily": round(float(returns.std() * 100), 4),
            "best_day": round(float(returns.max() * 100), 2),
            "worst_day": round(float(returns.min() * 100), 2),
            "positive_days": int((returns > 0).sum()),
            "negative_days": int((returns < 0).sum()),
            "win_rate": round(float((returns > 0).sum() / len(returns) * 100), 1) if len(returns) > 0 else 0,
        },
        "volume": {
            "mean": int(volume.mean()),
            "median": int(volume.median()),
            "max": int(volume.max()),
            "min": int(volume.min()),
        },
        "data_points": len(df),
        "date_range": {
            "start": str(df['Date'].iloc[0].date()) if 'Date' in df.columns else "N/A",
            "end": str(df['Date'].iloc[-1].date()) if 'Date' in df.columns else "N/A",
        }
    }


def get_advanced_risk_metrics(df: pd.DataFrame, benchmark_symbol: str = "^GSPC") -> dict:
    """Calculate advanced risk metrics: VaR, Sortino, Calmar, Beta, etc."""
    returns = df['Close'].pct_change().dropna()
    if len(returns) < 10:
        return {"error": "Insufficient data for risk metrics"}

    # Value at Risk (Historical)
    var_95 = round(float(np.percentile(returns, 5) * 100), 2)
    var_99 = round(float(np.percentile(returns, 1) * 100), 2)

    # Sortino Ratio (downside deviation)
    downside = returns[returns < 0]
    downside_std = float(downside.std() * np.sqrt(252)) if len(downside) > 0 else 0.001
    sortino = round(float((returns.mean() * 252) / downside_std), 2) if downside_std > 0 else 0

    # Calmar Ratio
    ann_return = float(returns.mean() * 252)
    max_dd = float((df['Close'] / df['Close'].cummax() - 1).min())
    calmar = round(ann_return / abs(max_dd), 2) if abs(max_dd) > 0.001 else 0

    # Beta vs benchmark
    beta = None
    try:
        import yfinance as yf
        bench = yf.download(benchmark_symbol, period="6mo", interval="1d", progress=False)
        if not bench.empty:
            bench_col = bench.columns
            if hasattr(bench_col, 'to_flat_index'):
                bench.columns = ['_'.join(col).strip() for col in bench.columns.to_flat_index()]
            bench.reset_index(inplace=True)
            # Find close column
            close_col = [c for c in bench.columns if 'close' in c.lower()]
            if close_col:
                bench_returns = bench[close_col[0]].pct_change().dropna()
                min_len = min(len(returns), len(bench_returns))
                if min_len > 10:
                    stock_r = returns.iloc[-min_len:].values
                    bench_r = bench_returns.iloc[-min_len:].values
                    cov = np.cov(stock_r, bench_r)
                    beta = round(float(cov[0, 1] / cov[1, 1]), 2) if cov[1, 1] > 0 else None
    except Exception as e:
        logger.warning(f"Beta calculation failed: {e}")

    # Volatility cone (annualized vol at different windows)
    vol_cone = {}
    for window in [5, 10, 21, 63]:
        if len(returns) >= window:
            rolling_vol = returns.rolling(window).std() * np.sqrt(252)
            vol_cone[f"{window}d"] = {
                "current": round(float(rolling_vol.iloc[-1] * 100), 2) if pd.notna(rolling_vol.iloc[-1]) else None,
                "mean": round(float(rolling_vol.mean() * 100), 2),
                "min": round(float(rolling_vol.min() * 100), 2),
                "max": round(float(rolling_vol.max() * 100), 2),
            }

    return {
        "var_95": var_95,
        "var_99": var_99,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "beta": beta,
        "volatility_cone": vol_cone,
        "ann_return_pct": round(ann_return * 100, 2),
    }


def get_drawdown_series(df: pd.DataFrame) -> list:
    """Calculate drawdown time series for charting."""
    cummax = df['Close'].cummax()
    drawdown = ((df['Close'] - cummax) / cummax) * 100

    result = []
    for i, (_, row) in enumerate(df.iterrows()):
        if 'Date' in df.columns:
            result.append({
                "time": int(row['Date'].timestamp()),
                "value": round(float(drawdown.iloc[i]), 2),
            })
    return result
