from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.market_data import fetch_stock_data, get_current_price, get_stock_info
from services.technical import (
    calculate_features, generate_signals, expert_risk_assessment, get_performance_metrics,
    get_returns_distribution, get_descriptive_stats, get_advanced_risk_metrics, get_drawdown_series,
)
from services.predictor import train_best_model, predict_next, train_ensemble, calculate_risk_score
from services.prediction_tracker import log_prediction
from services.unified_analyzer import compute_unified_verdict
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    symbol: str
    period: str = "1mo"
    interval: str = "1d"
    timeframe: str = "1d"  # for prediction tracking
    user_id: str | None = None


@router.post("/analyze")
async def analyze_stock(req: AnalyzeRequest):
    """Phase 1: Fast analysis — chart, signals, info, unified verdict (rule-based only). No ML (instant)."""
    symbol = req.symbol.upper().strip()
    if not symbol:
        raise HTTPException(400, "Symbol is required")

    # 1. Fetch display data
    data = fetch_stock_data(symbol, period=req.period, interval=req.interval)
    if data is None:
        raise HTTPException(404, f"No data found for {symbol}")

    # 2. Stock info
    info = get_stock_info(symbol)

    # 3. Current price
    current_price = get_current_price(symbol)
    if current_price is None:
        current_price = float(data['Close'].iloc[-1])

    # 4. Technical features
    # Ensure dataframe is sorted and deduplicated (chart safety)
    if 'Date' in data.columns:
        data = data.sort_values('Date').drop_duplicates(subset=['Date']).dropna(subset=['Open', 'High', 'Low', 'Close'])
        
    featured = calculate_features(data)

    # 5. Trading signals
    signals = generate_signals(featured)

    # 6. Expert risk assessment (rule-based — fast)
    expert_risk = expert_risk_assessment(featured)

    # 7. Performance metrics
    perf = get_performance_metrics(featured)

    # 8. Unified verdict (Phase 1: rule-based only — instant)
    unified_verdict = compute_unified_verdict(
        signals=signals,
        expert_risk=expert_risk,
    )

    # 9. Build chart data (OHLCV for frontend)
    chart_data = []
    for _, row in data.iterrows():
        try:
            chart_data.append({
                "time": int(row['Date'].timestamp()),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0,
            })
        except Exception as e:
            logger.warning(f"Skipping charting row due to bad formatting: {e}")
            continue

    # 10. Support / Resistance
    support_resistance = {
        "pivot": round(float(featured['Pivot'].iloc[-1]), 2) if 'Pivot' in featured else None,
        "r1": round(float(featured['R1'].iloc[-1]), 2) if 'R1' in featured else None,
        "s1": round(float(featured['S1'].iloc[-1]), 2) if 'S1' in featured else None,
    }

    prev_close = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
    price_change = round(((current_price - prev_close) / prev_close) * 100, 2)

    # 11. Indicator data for the Indicators tab (time-series)
    indicator_data = []
    for _, row in featured.iterrows():
        try:
            entry = {"time": int(row['Date'].timestamp())}
            for col in ['RSI', 'MACD', 'ma_5', 'ma_20', 'BB_upper', 'BB_middle', 'BB_lower', 'OBV', 'ATR', 'MFI']:
                val = row.get(col)
                if pd.notna(val):  # skip NaN safely
                    entry[col] = round(float(val), 4)
            indicator_data.append(entry)
        except Exception:
            continue

    return {
        "symbol": symbol,
        "info": info,
        "current_price": round(current_price, 2),
        "price_change": price_change,
        "signals": signals,
        "expert_risk": expert_risk,
        "unified_verdict": unified_verdict,
        "performance": perf,
        "support_resistance": support_resistance,
        "chart_data": chart_data,
        "indicator_data": indicator_data,
        "data_points": len(data),
    }


@router.post("/analyze/ml")
async def analyze_stock_ml(req: AnalyzeRequest):
    """Phase 2: Heavy ML analysis — prediction + ensemble risk + updated unified verdict."""
    symbol = req.symbol.upper().strip()
    if not symbol:
        raise HTTPException(400, "Symbol is required")

    # Fetch extended data for ML (need 60+ rows for reliable training)
    ml_period = "6mo" if req.interval == "1d" else "1mo"
    ml_data = fetch_stock_data(symbol, period=ml_period, interval=req.interval)
    if ml_data is None or len(ml_data) < 20:
        # Fallback to user-requested period
        ml_data = fetch_stock_data(symbol, period=req.period, interval=req.interval)
        if ml_data is None:
            raise HTTPException(404, f"No data found for {symbol}")

    current_price = get_current_price(symbol)
    if current_price is None:
        current_price = float(ml_data['Close'].iloc[-1])

    ml_featured = calculate_features(ml_data)

    # 1. Trading signals (needed for full unified verdict)
    signals = generate_signals(ml_featured)
    expert_risk = expert_risk_assessment(ml_featured)

    # 2. ML Prediction
    prediction = None
    try:
        model, scaler = train_best_model(ml_featured)
        if model and scaler:
            prediction = predict_next(model, scaler, ml_featured)
    except Exception as e:
        logger.warning(f"Prediction failed: {e}")

    # 3. Ensemble Risk Score
    risk_data = None
    try:
        ensemble = train_ensemble(ml_featured)
        if ensemble:
            risk_data = calculate_risk_score(ensemble, ml_featured, current_price)
    except Exception as e:
        logger.warning(f"Risk calc failed: {e}")

    # 4. Compute full unified verdict (now with ML data!)
    unified_verdict = compute_unified_verdict(
        signals=signals,
        prediction=prediction,
        risk_data=risk_data,
        expert_risk=expert_risk,
    )

    # 5. Log prediction if available and user is logged in
    prediction_logged = False
    if prediction and req.user_id:
        result = await log_prediction(
            req.user_id, symbol,
            prediction['predicted_price'],
            prediction['direction'],
            req.timeframe,
        )
        prediction_logged = result.get("logged", False)

    return {
        "symbol": symbol,
        "prediction": prediction,
        "prediction_logged": prediction_logged,
        "risk": risk_data,
        "unified_verdict": unified_verdict,
    }


@router.post("/analyze/data")
async def analyze_data(req: AnalyzeRequest):
    """Data & Statistics endpoint — raw data, stats, distributions, advanced risk."""
    symbol = req.symbol.upper().strip()
    if not symbol:
        raise HTTPException(400, "Symbol is required")

    # Fetch extended data for better stats
    data = fetch_stock_data(symbol, period=req.period, interval=req.interval)
    if data is None:
        raise HTTPException(404, f"No data found for {symbol}")

    featured = calculate_features(data)

    # Raw OHLCV table (last 100 rows max for performance)
    table_data = []
    for _, row in data.tail(100).iterrows():
        table_data.append({
            "date": str(row['Date'].date()) if hasattr(row['Date'], 'date') else str(row['Date']),
            "open": round(float(row['Open']), 2),
            "high": round(float(row['High']), 2),
            "low": round(float(row['Low']), 2),
            "close": round(float(row['Close']), 2),
            "volume": int(row['Volume']),
            "change_pct": round(float((row['Close'] - row['Open']) / row['Open'] * 100), 2) if row['Open'] > 0 else 0,
        })

    # Descriptive stats
    stats = get_descriptive_stats(data)

    # Returns distribution
    distribution = get_returns_distribution(data)

    # Advanced risk metrics
    advanced_risk = get_advanced_risk_metrics(featured)

    # Drawdown series
    drawdown = get_drawdown_series(data)

    return {
        "symbol": symbol,
        "table_data": table_data,
        "stats": stats,
        "distribution": distribution,
        "advanced_risk": advanced_risk,
        "drawdown": drawdown,
    }
