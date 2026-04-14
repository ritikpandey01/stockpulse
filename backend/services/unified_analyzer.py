"""
Unified Analysis Engine — merges all signal sources into a single coherent verdict.
Eliminates conflicts between rule-based and ML predictions.
"""
import logging

logger = logging.getLogger(__name__)

# Weight distribution for unified scoring
WEIGHTS = {
    "technical": 0.35,
    "ml_prediction": 0.30,
    "ensemble_risk": 0.20,
    "sentiment": 0.15,
}


def normalize_technical_score(signals: dict) -> float:
    """Convert technical signal score (-4 to +4) to normalized (-100 to +100)."""
    raw = signals.get("score", 0)
    return max(-100, min(100, raw * 25))  # maps -4..+4 → -100..+100


def normalize_prediction_score(prediction: dict | None) -> float:
    """Convert ML prediction change_percent to normalized (-100 to +100)."""
    if prediction is None:
        return 0.0
    change = prediction.get("change_percent", 0)
    # Cap at ±10% change → maps to ±100
    return max(-100, min(100, change * 10))


def normalize_risk_score(risk_data: dict | None) -> float:
    """Convert ensemble risk (0-100, higher = riskier) to directional score.
    High risk → bearish (negative), Low risk → bullish (positive)."""
    if risk_data is None:
        return 0.0
    risk = risk_data.get("risk_score", 50)
    change = risk_data.get("change_percent", 0)

    # Use both risk score and predicted direction
    # Risk score 0 = very safe (+50), Risk score 100 = very dangerous (-100)
    risk_component = 50 - risk  # 0→+50, 50→0, 100→−50

    # Direction from ensemble model predictions
    direction_component = max(-50, min(50, change * 5))

    return max(-100, min(100, risk_component + direction_component))


def normalize_sentiment_score(sentiment: dict | None) -> float:
    """Convert sentiment score (0-100 greed/fear) to normalized (-100 to +100)."""
    if sentiment is None:
        return 0.0
    score = sentiment.get("score", 50)
    # 0 = extreme fear → -100, 50 = neutral → 0, 100 = extreme greed → +100
    return (score - 50) * 2


def _get_verdict_label(score: float) -> str:
    """Convert unified score to human-readable verdict."""
    if score >= 40:
        return "Strong Bullish"
    elif score >= 20:
        return "Bullish"
    elif score >= 5:
        return "Slightly Bullish"
    elif score >= -5:
        return "Neutral"
    elif score >= -20:
        return "Slightly Bearish"
    elif score >= -40:
        return "Bearish"
    else:
        return "Strong Bearish"


def _get_component_label(score: float) -> str:
    """Get direction label for a single component."""
    if score >= 20:
        return "Bullish"
    elif score > -20:
        return "Neutral"
    else:
        return "Bearish"


def _calculate_confidence(components: dict[str, float]) -> float:
    """Calculate confidence based on agreement between components.
    High agreement → high confidence. Disagreement → low confidence."""
    active = {k: v for k, v in components.items() if v != 0.0}
    if len(active) <= 1:
        return 50.0  # Can't assess agreement with 0-1 sources

    values = list(active.values())
    # Check if all agree on direction
    all_bullish = all(v > 0 for v in values)
    all_bearish = all(v < 0 for v in values)
    all_agree = all_bullish or all_bearish

    if all_agree:
        # Strong agreement → high confidence, scaled by magnitude
        avg_magnitude = sum(abs(v) for v in values) / len(values)
        return min(95, 60 + avg_magnitude * 0.35)

    # Mixed signals → lower confidence
    bullish_count = sum(1 for v in values if v > 5)
    bearish_count = sum(1 for v in values if v < -5)
    neutral_count = len(values) - bullish_count - bearish_count

    # The more disagreement, the lower confidence
    if bullish_count > 0 and bearish_count > 0:
        # Direct conflict
        spread = max(values) - min(values)
        return max(20, 55 - spread * 0.2)

    return 55.0 + neutral_count * 5


def _build_explanation(
    components: dict[str, float],
    signals: dict | None,
    prediction: dict | None,
    risk_data: dict | None,
    sentiment: dict | None,
    confidence: float,
) -> list[str]:
    """Build human-readable explanation for the unified verdict."""
    explanation = []

    # Technical explanation
    tech_score = components.get("technical", 0)
    if signals:
        if tech_score > 20:
            explanation.append(
                f"Technical indicators are bullish (MACD: {signals.get('macd', 'N/A')}, "
                f"RSI: {signals.get('rsi', {}).get('value', 'N/A')}, "
                f"BB: {signals.get('bollinger', 'N/A')})"
            )
        elif tech_score < -20:
            explanation.append(
                f"Technical indicators are bearish (MACD: {signals.get('macd', 'N/A')}, "
                f"RSI: {signals.get('rsi', {}).get('value', 'N/A')}, "
                f"BB: {signals.get('bollinger', 'N/A')})"
            )
        else:
            explanation.append("Technical indicators are neutral — no strong directional signal")

    # ML Prediction explanation
    ml_score = components.get("ml_prediction", 0)
    if prediction:
        direction = prediction.get("direction", "N/A")
        change = prediction.get("change_percent", 0)
        explanation.append(
            f"ML models predict {abs(change):.2f}% {'upside' if direction == 'UP' else 'downside'} "
            f"(target: ${prediction.get('predicted_price', 'N/A')})"
        )

    # Risk explanation
    risk_score_val = components.get("ensemble_risk", 0)
    if risk_data:
        explanation.append(
            f"Ensemble risk assessment: {risk_data.get('risk_class', 'N/A')} risk "
            f"(score: {risk_data.get('risk_score', 'N/A')}/100)"
        )

    # Sentiment explanation
    sent_score = components.get("sentiment", 0)
    if sentiment and sentiment.get("score", 50) != 50:
        explanation.append(
            f"News sentiment: {sentiment.get('mood', 'Neutral')} "
            f"(score: {sentiment.get('score', 50)}/100)"
        )

    # Conflict explanation
    active = {k: v for k, v in components.items() if abs(v) > 10}
    bullish = [k for k, v in active.items() if v > 10]
    bearish = [k for k, v in active.items() if v < -10]

    if bullish and bearish:
        bull_names = [k.replace("_", " ").title() for k in bullish]
        bear_names = [k.replace("_", " ").title() for k in bearish]
        explanation.append(
            f"⚠️ Mixed signals: {', '.join(bull_names)} pointing up while "
            f"{', '.join(bear_names)} pointing down. "
            f"Confidence is {'low' if confidence < 40 else 'moderate'} — consider waiting for confirmation."
        )

    return explanation


def compute_unified_verdict(
    signals: dict | None = None,
    prediction: dict | None = None,
    risk_data: dict | None = None,
    sentiment: dict | None = None,
    expert_risk: dict | None = None,
) -> dict:
    """
    Compute the unified analysis verdict by merging all signal sources.

    Returns a complete verdict dict with:
    - direction: "Bullish" / "Bearish" / "Neutral" etc.
    - score: -100 to +100
    - confidence: 0-100%
    - explanation: list of human-readable reasons
    - components: breakdown of each signal source
    """
    # Step 1: Normalize each component
    components = {}
    active_weights = {}

    if signals:
        components["technical"] = normalize_technical_score(signals)
        active_weights["technical"] = WEIGHTS["technical"]

    if prediction:
        components["ml_prediction"] = normalize_prediction_score(prediction)
        active_weights["ml_prediction"] = WEIGHTS["ml_prediction"]

    if risk_data:
        components["ensemble_risk"] = normalize_risk_score(risk_data)
        active_weights["ensemble_risk"] = WEIGHTS["ensemble_risk"]

    if sentiment and sentiment.get("confidence", 0) > 0:
        components["sentiment"] = normalize_sentiment_score(sentiment)
        active_weights["sentiment"] = WEIGHTS["sentiment"]

    # Step 2: Weighted average (re-normalize weights for active components)
    if not active_weights:
        return {
            "direction": "Neutral",
            "score": 0,
            "confidence": 0,
            "explanation": ["Insufficient data for analysis"],
            "components": {},
            "verdict_label": "Neutral",
        }

    total_weight = sum(active_weights.values())
    unified_score = sum(
        components[k] * (active_weights[k] / total_weight)
        for k in components
    )

    # Step 3: Calculate confidence
    confidence = _calculate_confidence(components)

    # Step 4: Derive verdict
    verdict_label = _get_verdict_label(unified_score)

    # Step 5: Build component breakdown for UI
    component_breakdown = {}
    for key, score in components.items():
        component_breakdown[key] = {
            "score": round(score, 1),
            "weight": round(active_weights.get(key, 0) / total_weight * 100, 1),
            "direction": _get_component_label(score),
        }

    # Step 6: Build explanation
    explanation = _build_explanation(
        components, signals, prediction, risk_data, sentiment, confidence
    )

    # Step 7: Risk summary (merge expert + ensemble into one)
    risk_summary = None
    if risk_data or expert_risk:
        risk_scores = []
        risk_factors = []
        if risk_data:
            risk_scores.append(risk_data.get("risk_score", 50))
            risk_factors.extend(risk_data.get("explanation", []))
        if expert_risk:
            risk_scores.append(expert_risk.get("score", 50))
            risk_factors.extend(expert_risk.get("factors", []))

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 50
        if avg_risk >= 60:
            risk_class = "HIGH"
        elif avg_risk >= 30:
            risk_class = "MEDIUM"
        else:
            risk_class = "LOW"

        risk_summary = {
            "score": round(avg_risk, 1),
            "class": risk_class,
            "factors": risk_factors[:6],  # Cap at 6 factors
        }

    return {
        "direction": "Bullish" if unified_score > 5 else ("Bearish" if unified_score < -5 else "Neutral"),
        "verdict_label": verdict_label,
        "score": round(unified_score, 1),
        "confidence": round(confidence, 1),
        "explanation": explanation,
        "components": component_breakdown,
        "risk_summary": risk_summary,
    }
