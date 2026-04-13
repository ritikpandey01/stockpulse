from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.market_data import fetch_stock_data, get_current_price, get_stock_info
from services.technical import calculate_features, generate_signals, expert_risk_assessment, get_performance_metrics
from services.predictor import train_best_model, predict_next, train_ensemble, calculate_risk_score
from services.prediction_tracker import log_prediction

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
    """Phase 1: Fast analysis — chart, signals, info, expert risk. No ML (instant)."""
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
    featured = calculate_features(data)

    # 5. Trading signals
    signals = generate_signals(featured)

    # 6. Expert risk assessment (rule-based — fast)
    expert_risk = expert_risk_assessment(featured)

    # 7. Performance metrics
    perf = get_performance_metrics(featured)

    # 8. Build chart data (OHLCV for frontend)
    chart_data = []
    for _, row in data.iterrows():
        chart_data.append({
            "time": int(row['Date'].timestamp()),
            "open": round(float(row['Open']), 2),
            "high": round(float(row['High']), 2),
            "low": round(float(row['Low']), 2),
            "close": round(float(row['Close']), 2),
            "volume": int(row['Volume']),
        })

    # 9. Support / Resistance
    support_resistance = {
        "pivot": round(float(featured['Pivot'].iloc[-1]), 2) if 'Pivot' in featured else None,
        "r1": round(float(featured['R1'].iloc[-1]), 2) if 'R1' in featured else None,
        "s1": round(float(featured['S1'].iloc[-1]), 2) if 'S1' in featured else None,
    }

    prev_close = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
    price_change = round(((current_price - prev_close) / prev_close) * 100, 2)

    # 10. Indicator data for the Indicators tab (time-series)
    indicator_data = []
    for _, row in featured.iterrows():
        entry = {"time": int(row['Date'].timestamp())}
        for col in ['RSI', 'MACD', 'ma_5', 'ma_20', 'BB_upper', 'BB_middle', 'BB_lower', 'OBV', 'ATR', 'MFI']:
            val = row.get(col)
            if val is not None and not (isinstance(val, float) and (val != val)):  # skip NaN
                entry[col] = round(float(val), 4)
        indicator_data.append(entry)

    return {
        "symbol": symbol,
        "info": info,
        "current_price": round(current_price, 2),
        "price_change": price_change,
        "signals": signals,
        "expert_risk": expert_risk,
        "performance": perf,
        "support_resistance": support_resistance,
        "chart_data": chart_data,
        "indicator_data": indicator_data,
        "data_points": len(data),
    }


@router.post("/analyze/ml")
async def analyze_stock_ml(req: AnalyzeRequest):
    """Phase 2: Heavy ML analysis — prediction + ensemble risk. Called async after Phase 1."""
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

    # 1. ML Prediction
    prediction = None
    try:
        model, scaler = train_best_model(ml_featured)
        if model and scaler:
            prediction = predict_next(model, scaler, ml_featured)
    except Exception as e:
        logger.warning(f"Prediction failed: {e}")

    # 2. Ensemble Risk Score
    risk_data = None
    try:
        ensemble = train_ensemble(ml_featured)
        if ensemble:
            risk_data = calculate_risk_score(ensemble, ml_featured, current_price)
    except Exception as e:
        logger.warning(f"Risk calc failed: {e}")

    # 3. Log prediction if available and user is logged in
    prediction_logged = False
    if prediction and req.user_id:
        result = await log_prediction(
            req.user_id, symbol,
            prediction['predicted_price'],
            prediction['direction'],
            req.timeframe,
        )
        prediction_logged = result.get("logged", False)

    # Async save history
    return {
        "symbol": symbol,
        "prediction": prediction,
        "prediction_logged": prediction_logged,
        "risk": risk_data,
    }
