import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
# from xgboost import XGBRegressor
# from catboost import CatBoostRegressor  # type: ignore

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    'prev_open', 'prev_high', 'prev_low', 'prev_vol',
    'Lag1', 'Lag2', 'ma_10', 'RSI', 'MACD', 'BB_middle', 'OBV', 'Pivot'
]


def _prepare_data(df: pd.DataFrame):
    """Clean data and split features/target."""
    clean = df.dropna(subset=FEATURE_COLS + ['Close'])
    if clean.shape[0] < 5:
        return None, None
    X = clean[FEATURE_COLS].values
    y = clean['Close'].values
    return X, y


def train_best_model(df: pd.DataFrame):
    """Auto-select best model via GridSearchCV. Ported from price/model.py."""
    X, y = _prepare_data(df)
    if X is None:
        return None, None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_splits = min(5, len(X_scaled) - 1)
    if n_splits < 2:
        n_splits = 2

    models = {
        'ridge': (Ridge(), {'alpha': [0.1, 1, 10]}),
        'lasso': (Lasso(), {'alpha': [0.1, 1, 10]}),
        'random_forest': (RandomForestRegressor(random_state=42), {'n_estimators': [50, 100], 'max_depth': [5, 10]}),
        'gradient_boosting': (GradientBoostingRegressor(random_state=42), {'n_estimators': [50, 100], 'learning_rate': [0.05, 0.1]}),
        # 'xgboost': (XGBRegressor(random_state=42, verbosity=0), {'n_estimators': [50, 100], 'learning_rate': [0.05, 0.1]}),
        # 'catboost': (CatBoostRegressor(verbose=0, random_state=42), {'iterations': [50, 100], 'learning_rate': [0.05, 0.1]}),
    }

    best_model = None
    best_score = float('-inf')

    for name, (model, params) in models.items():
        try:
            gs = GridSearchCV(
                model, params,
                cv=TimeSeriesSplit(n_splits=n_splits),
                scoring='neg_mean_squared_error',
                n_jobs=-1,
            )
            gs.fit(X_scaled, y)
            if gs.best_score_ > best_score:
                best_score = gs.best_score_
                best_model = gs.best_estimator_
                logger.info(f"New best: {name} score={best_score:.4f}")
        except Exception as e:
            logger.warning(f"Skipping {name}: {e}")

    if best_model is None:
        # Fallback to simple ridge
        best_model = Ridge(alpha=1.0)
        best_model.fit(X_scaled, y)

    return best_model, scaler


def predict_next(model, scaler, df: pd.DataFrame) -> dict | None:
    """Predict next period price."""
    try:
        latest = df.iloc[-1]
        next_features = pd.DataFrame([{
            'prev_open': latest['Open'],
            'prev_high': latest['High'],
            'prev_low': latest['Low'],
            'prev_vol': latest['Volume'],
            'Lag1': latest['Close'],
            'Lag2': latest.get('Lag1', latest['Close']),
            'ma_10': df['Close'].tail(10).mean(),
            'RSI': latest.get('RSI', 50),
            'MACD': latest.get('MACD', 0),
            'BB_middle': latest.get('BB_middle', latest['Close']),
            'OBV': latest.get('OBV', 0),
            'Pivot': latest.get('Pivot', latest['Close']),
        }])

        X_scaled = scaler.transform(next_features[FEATURE_COLS].values)
        predicted = float(model.predict(X_scaled)[0])
        current = float(latest['Close'])
        change_pct = ((predicted - current) / current) * 100
        direction = "UP" if predicted > current else "DOWN"

        return {
            "predicted_price": round(predicted, 2),
            "current_price": round(current, 2),
            "change_percent": round(change_pct, 2),
            "direction": direction,
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None


def train_ensemble(df: pd.DataFrame) -> dict | None:
    """Train 8-model ensemble for risk scoring. Ported from risk/model.py."""
    X, y = _prepare_data(df)
    if X is None:
        return None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    models = {
        'Linear': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=1.0),
        'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        'SVR': SVR(C=1.0, kernel='rbf'),
        # 'XGBoost': XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42, verbosity=0),
        # 'CatBoost': CatBoostRegressor(n_estimators=100, learning_rate=0.1, verbose=0, random_state=42),
    }

    trained = {}
    scores = {}
    for name, model in models.items():
        try:
            model.fit(X_scaled, y)
            scores[name] = round(model.score(X_scaled, y), 4)
            trained[name] = model
        except Exception as e:
            logger.warning(f"Ensemble skip {name}: {e}")

    # Feature importance from tree models
    importance = {}
    for tree_name in ['Random Forest']:
        if tree_name in trained:
            imp = trained[tree_name].feature_importances_
            for i, col in enumerate(FEATURE_COLS):
                importance[col] = round(float(imp[i]) * 100, 1)
            break

    return {
        'models': trained,
        'scaler': scaler,
        'scores': scores,
        'feature_importance': dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)),
    }


def calculate_risk_score(ensemble: dict, df: pd.DataFrame, current_price: float) -> dict | None:
    """Calculate ensemble risk score. Ported from risk/model.py."""
    try:
        latest = df.iloc[-1]
        next_features = pd.DataFrame([{
            'prev_open': latest['Open'],
            'prev_high': latest['High'],
            'prev_low': latest['Low'],
            'prev_vol': latest['Volume'],
            'Lag1': latest['Close'],
            'Lag2': latest.get('Lag1', latest['Close']),
            'ma_10': df['Close'].tail(10).mean(),
            'RSI': latest.get('RSI', 50),
            'MACD': latest.get('MACD', 0),
            'BB_middle': latest.get('BB_middle', latest['Close']),
            'OBV': latest.get('OBV', 0),
            'Pivot': latest.get('Pivot', latest['Close']),
        }])

        scaler = ensemble['scaler']
        X = scaler.transform(next_features[FEATURE_COLS].values)

        predictions = {}
        for name, model in ensemble['models'].items():
            predictions[name] = float(model.predict(X)[0])

        predicted_price = np.mean(list(predictions.values()))
        change_pct = ((predicted_price - current_price) / current_price) * 100

        # Risk from price direction
        if change_pct < 0:
            risk_from_price = min(100, abs(change_pct) * 20)
        else:
            risk_from_price = max(0, 40 - change_pct * 5)

        # Volatility risk
        vol = df['Close'].pct_change().std() * 100
        risk_from_vol = min(40, vol * 200)

        # RSI risk
        rsi = float(latest.get('RSI', 50)) if pd.notna(latest.get('RSI')) else 50
        rsi_risk = 0
        if rsi > 70:
            rsi_risk = (rsi - 70) * 1.5
        elif rsi < 30:
            rsi_risk = (30 - rsi) * 1.5

        total = risk_from_price * 0.5 + risk_from_vol * 0.3 + rsi_risk * 0.2
        risk_score = min(100, max(0, total))

        risk_class = "LOW" if risk_score < 30 else ("MEDIUM" if risk_score < 60 else "HIGH")

        # Model votes
        votes = {}
        for name, pred in predictions.items():
            pct = ((pred - current_price) / current_price) * 100
            votes[name] = "HIGH" if pct < -2 else ("MEDIUM" if pct < 0 else "LOW")

        # Explanation
        explanation = []
        if change_pct < -2:
            explanation.append(f"Models predict {abs(change_pct):.2f}% downside")
        elif change_pct < 0:
            explanation.append(f"Models predict moderate {abs(change_pct):.2f}% downside")
        else:
            explanation.append(f"Models predict {change_pct:.2f}% upside potential")

        if rsi > 70:
            explanation.append(f"RSI overbought at {rsi:.1f}")
        elif rsi < 30:
            explanation.append(f"RSI oversold at {rsi:.1f} — potential reversal")

        return {
            "risk_score": round(risk_score, 1),
            "risk_class": risk_class,
            "predicted_price": round(predicted_price, 2),
            "change_percent": round(change_pct, 2),
            "model_votes": votes,
            "model_scores": ensemble['scores'],
            "feature_importance": ensemble['feature_importance'],
            "explanation": explanation,
            "downside_prob": round(min(100, risk_score * 1.2) if change_pct < 0 else max(0, risk_score * 0.8), 1),
        }
    except Exception as e:
        logger.error(f"Risk score error: {e}")
        return None
