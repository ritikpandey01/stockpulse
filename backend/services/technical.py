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
