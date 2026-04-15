<p align="center">
  <img src="https://img.shields.io/badge/⚡_StockPulse-v3.0-0D1117?style=for-the-badge&labelColor=0D1117" alt="StockPulse v3.0"/>
</p>

<h1 align="center">⚡ StockPulse</h1>
<p align="center"><b>AI-Powered Unified Stock Analysis Platform</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Scikit--Learn-1.5-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="Scikit-Learn"/>
  <img src="https://img.shields.io/badge/Supabase-Auth_&_DB-3ECF8E?style=flat-square&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/Vanilla_JS-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript"/>
  <img src="https://img.shields.io/badge/5,600+_Lines-of_Code-blue?style=flat-square" alt="Lines of Code"/>
</p>

<p align="center">
  <i>A comprehensive trading intelligence platform that merges technical indicators, machine learning predictions, ensemble risk scoring, and real-time news sentiment into a single, explainable <b>StockPulse Score</b>.</i>
</p>

---

## 📑 Table of Contents

- [✨ Highlights](#-highlights)
- [🧠 The Unified Analysis Engine](#-the-unified-analysis-engine)
- [🖥️ Dashboard & UI](#️-dashboard--ui)
- [🏗️ System Architecture](#️-system-architecture)
- [📂 Project Structure](#-project-structure)
- [🛠️ Tech Stack](#️-tech-stack)
- [🔌 API Reference](#-api-reference)
- [🚀 Getting Started](#-getting-started)
- [🧪 How We Built It](#-how-we-built-it)
- [📈 Future Roadmap](#-future-roadmap)

---

## ✨ Highlights

| Feature | Description |
| :--- | :--- |
| **Unified StockPulse Score** | A single weighted verdict (-100 to +100) that resolves conflicts between technical, ML, risk, and sentiment signals |
| **Progressive Loading** | Phase 1 (instant rule-based) → Phase 2 (async ML training) → Phase 3 (async sentiment) — the UI never blocks |
| **6-Model ML Ensemble** | Ridge, Lasso, Random Forest, Gradient Boosting, SVR, Linear Regression — auto-selected via `GridSearchCV` with `TimeSeriesSplit` |
| **Expert Risk System** | Dual-layer risk: rule-based expert assessment + ensemble-based quantitative risk scoring |
| **LLM Sentiment Analysis** | Groq-powered (Llama 3.3 70B) analysis of real-time news fetched via Tavily |
| **Interactive Charting** | Lightweight Charts library with candlestick, volume, RSI, MACD, Bollinger Bands, OBV mini-charts |
| **Stock Screener** | Filter 60+ stocks by sector, price, RSI, signal, and sort by composite score |
| **Stock Comparator** | Side-by-side normalized returns, correlation matrices, and key metric comparison for up to 5 stocks |
| **Fundamentals Deep Dive** | Valuation, profitability, financial health, analyst targets, dividends — all in one view |
| **Advanced Risk Metrics** | VaR (95%/99%), Sortino ratio, Calmar ratio, Beta vs S&P 500, volatility cone |
| **Fear & Greed Index** | Composite market sentiment derived from VIX, S&P 500 momentum, and sector breadth |
| **Prediction Accuracy Tracker** | Every ML prediction is logged to Supabase and validated against actual outcomes |
| **Auth & Admin Panel** | Supabase authentication with role-based admin access to accuracy dashboards |

---

## 🧠 The Unified Analysis Engine

The core innovation of StockPulse is the **Unified Analysis Engine** (`unified_analyzer.py`). Instead of showing users conflicting Buy/Sell signals from different sources, it aggregates everything into a single, weighted verdict with full explainability.

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                             │
│                                                                 │
│  📊 Technical Signals    🤖 ML Prediction    ⚠️ Ensemble Risk   │
│  (MACD, RSI, BB, OBV)   (6-model ensemble)  (price + vol +    │
│  Score: -4 to +4         Change: ±X%         RSI composite)    │
│                                                                 │
│  📰 News Sentiment                                             │
│  (Groq LLM analysis of Tavily search results)                  │
└──────────────┬──────────────┬──────────────┬──────────────┬─────┘
               │              │              │              │
               ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│              NORMALIZATION LAYER (-100 to +100)                 │
│                                                                 │
│  Technical:  score × 25        ML:  change% × 10               │
│  Risk:  (50 - risk) + (Δ × 5)  Sentiment:  (score - 50) × 2   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              WEIGHTED AGGREGATION                               │
│                                                                 │
│  Technical:     35%  ████████████░░░░░░░░░░░░░░░░░░            │
│  ML Prediction: 30%  ██████████░░░░░░░░░░░░░░░░░░░░            │
│  Ensemble Risk: 20%  ███████░░░░░░░░░░░░░░░░░░░░░░░            │
│  Sentiment:     15%  █████░░░░░░░░░░░░░░░░░░░░░░░░░            │
│                                                                 │
│  Weights auto-redistribute when sources are unavailable         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED OUTPUT                               │
│                                                                 │
│  Score: -100 ◄──────────── 0 ────────────► +100                │
│  Verdict: Strong Bearish → Bearish → Neutral → Bullish → ...  │
│  Confidence: Based on inter-component agreement                 │
│  Explanation: Human-readable reasons for each factor            │
│  Risk Summary: Merged expert + ensemble risk with factors       │
└─────────────────────────────────────────────────────────────────┘
```

### Conflict Resolution

When signals disagree (e.g., RSI says "Buy" but ML predicts downside), StockPulse doesn't hide the conflict — it **explains** it:

```
⚠️ Mixed signals: Technical pointing up while ML Prediction pointing down.
   Confidence is low — consider waiting for confirmation.
```

### Verdict Scale

| Score Range | Verdict Label |
|:-----------:|:-------------|
| +40 to +100 | 🟢 Strong Bullish |
| +20 to +39 | 🟢 Bullish |
| +5 to +19 | 🟢 Slightly Bullish |
| -4 to +4 | 🟡 Neutral |
| -19 to -5 | 🔴 Slightly Bearish |
| -39 to -20 | 🔴 Bearish |
| -100 to -40 | 🔴 Strong Bearish |

---

## 🖥️ Dashboard & UI

The frontend is a **5-tab glassmorphism interface** built with pure HTML/CSS/JS (no frameworks), designed for speed and clarity:

### Pages

| Page | Purpose |
|:-----|:--------|
| **📊 Dashboard** | Market overview (indices, Fear & Greed gauge, sector heatmap, AI top picks) |
| **🔍 Analyze** | Deep-dive into any stock with the 5-tab analysis view |
| **🎯 Screener** | Filter 60+ stocks with multi-criteria filtering |
| **⚖️ Compare** | Side-by-side analysis of 2–5 stocks |
| **👑 Admin** | Prediction accuracy tracker (admin-only) |

### Analyze Tabs

1. **📈 Chart** — Interactive candlestick + volume chart with support/resistance levels
2. **📊 Technical** — RSI, MACD, Bollinger Bands, OBV mini-charts + signal breakdown + expert risk factors
3. **🔮 Prediction** — ML price prediction + ensemble risk assessment + model votes
4. **🏛 Fundamentals** — Valuation, profitability, analyst targets, financial health, dividends, price info
5. **📋 Data & Stats** — Descriptive statistics, returns distribution, advanced risk metrics (VaR, Sortino, Beta), volatility cone, drawdown chart, OHLCV table

### Progressive Loading Architecture

The UI uses a **3-phase progressive loading** strategy so users never wait:

```
Phase 1 (Instant)  → Rule-based signals, chart, support/resistance, expert risk
Phase 2 (Async)    → ML model training + prediction + ensemble risk → verdict auto-updates
Phase 3 (Async)    → News sentiment analysis via Groq LLM
```

The unified verdict card shows a live spinner (`"ML models loading — verdict will update..."`) and seamlessly replaces itself when Phase 2 completes.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vanilla JS)                      │
│                                                                    │
│  index.html ── style.css ── api.js ── charts.js ── app.js         │
│                              auth.js ── admin.js                   │
│                                                                    │
│  Lightweight Charts │ Glassmorphism UI │ Progressive Loading       │
└────────────────────────────────┬───────────────────────────────────┘
                                 │  fetch() API calls
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                      FastAPI BACKEND (Python)                      │
│                                                                    │
│  main.py ─── Routes ─────────────────────────────────────────┐    │
│              │                                                │    │
│              ├─ /api/analyze      (POST) Phase 1: fast        │    │
│              ├─ /api/analyze/ml   (POST) Phase 2: ML          │    │
│              ├─ /api/analyze/data (POST) Stats & risk         │    │
│              ├─ /api/sentiment    (GET)  News + LLM           │    │
│              ├─ /api/fundamentals (GET)  Corporate data       │    │
│              ├─ /api/screener     (GET)  Multi-stock filter   │    │
│              ├─ /api/compare      (POST) Side-by-side         │    │
│              ├─ /api/market/*     (GET)  Overview/heatmap     │    │
│              ├─ /api/recommendations (GET) AI top picks       │    │
│              ├─ /api/auth/*       (POST) Login/Signup         │    │
│              └─ /api/admin/*      (GET)  Accuracy tracker     │    │
│                                                                    │
│  Services ───────────────────────────────────────────────────┐    │
│  │ market_data.py      │ technical.py       │ predictor.py   │    │
│  │ unified_analyzer.py │ news_sentiment.py  │ recommender.py │    │
│  │ screener.py         │ comparison.py      │ fundamentals.py│    │
│  │ market_overview.py  │ prediction_tracker │ auth.py        │    │
│  │ database.py         │                    │                │    │
│  └───────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ yfinance │ │ Supabase │ │  Groq +  │
              │ (Market  │ │ (Auth +  │ │  Tavily  │
              │  Data)   │ │  DB)     │ │  (NLP)   │
              └──────────┘ └──────────┘ └──────────┘
```

---

## 📂 Project Structure

```
stockpulse/
│
├── backend/
│   ├── main.py                    # FastAPI app, CORS, route registration, static serving
│   ├── config.py                  # Environment variable loader (.env)
│   │
│   ├── routes/
│   │   ├── analysis.py            # /analyze, /analyze/ml, /analyze/data endpoints
│   │   ├── sentiment.py           # /sentiment/:symbol endpoint
│   │   ├── recommendations.py     # /recommendations endpoint
│   │   ├── market.py              # /market/overview endpoint
│   │   ├── fundamentals.py        # /fundamentals/:symbol endpoint
│   │   ├── screener.py            # /screener endpoint with query filters
│   │   ├── comparison.py          # /compare endpoint
│   │   ├── auth.py                # /auth/login, /auth/signup, /auth/me
│   │   ├── admin.py               # /admin/accuracy, /admin/validate
│   │   └── history.py             # /history endpoint (search logging)
│   │
│   └── services/
│       ├── market_data.py         # yfinance data fetching (OHLCV, info, price)
│       ├── technical.py           # 20+ indicator calculation, signal generation,
│       │                          #   expert risk system, performance metrics,
│       │                          #   advanced risk (VaR, Sortino, Beta), drawdowns
│       ├── predictor.py           # ML pipeline: GridSearchCV model selection,
│       │                          #   6-model ensemble training, risk scoring
│       ├── unified_analyzer.py    # ★ Core: weighted verdict engine with
│       │                          #   normalization, confidence, explainability
│       ├── news_sentiment.py      # Tavily search → Groq LLM sentiment analysis
│       ├── recommender.py         # Watchlist scoring + top picks generation
│       ├── screener.py            # 60-stock universe screening with filters
│       ├── comparison.py          # Multi-stock normalized returns + correlation
│       ├── fundamentals.py        # Comprehensive corporate financial data
│       ├── market_overview.py     # Indices, sector heatmap, Fear & Greed calc
│       ├── prediction_tracker.py  # Log predictions to DB + validate vs actuals
│       ├── auth.py                # Supabase auth (signup, login, token verify)
│       └── database.py            # Supabase client singleton
│
├── frontend/
│   ├── index.html                 # Single-page app: sidebar, all 5 pages, modals
│   ├── css/
│   │   └── style.css              # Complete design system (glassmorphism, dark theme,
│   │                              #   animations, responsive grid, verdict components)
│   └── js/
│       ├── api.js                 # Fetch wrapper with auth token injection
│       ├── charts.js              # Lightweight Charts: candlestick, RSI, MACD, BB, OBV
│       ├── app.js                 # ★ Core: navigation, progressive analysis,
│       │                          #   unified verdict renderer, screener, comparator,
│       │                          #   fundamentals builder, data & stats renderer
│       ├── auth.js                # Login/signup modal, session management
│       └── admin.js               # Admin accuracy dashboard renderer
│
├── README.md                      # You are here
└── backend/
    ├── requirements.txt           # Python dependencies (15 packages)
    ├── supabase_schema.sql        # DB schema: predictions + search_history tables
    ├── test.py                    # Test scripts
    └── test_analyze.py            # Analysis testing
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|:-----------|:--------|
| **FastAPI** | High-performance async API framework |
| **Uvicorn** | ASGI server |
| **Pydantic** | Request/response validation |
| **yfinance** | Real-time & historical market data |
| **pandas / numpy** | Data manipulation & numerical computation |
| **scikit-learn** | ML models (Ridge, Lasso, RF, GBR, SVR), GridSearchCV, TimeSeriesSplit |
| **ta** (Technical Analysis) | 20+ indicators (RSI, MACD, Bollinger, ATR, MFI, OBV) |
| **Groq** | LLM API (Llama 3.3 70B) for sentiment analysis |
| **Tavily** | Real-time news search API |
| **Supabase** | PostgreSQL database + authentication |
| **httpx** | Async HTTP client |

### Frontend
| Technology | Purpose |
|:-----------|:--------|
| **HTML5 / CSS3** | Semantic structure, glassmorphism design system |
| **Vanilla JavaScript (ES6+)** | Zero-dependency application logic |
| **Lightweight Charts** | TradingView-grade interactive financial charts |
| **Inter + JetBrains Mono** | Typography (Google Fonts) |

---

## 🔌 API Reference

### Analysis Endpoints

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `POST` | `/api/analyze` | **Phase 1**: Chart data, technical signals, expert risk, instant unified verdict |
| `POST` | `/api/analyze/ml` | **Phase 2**: ML prediction, ensemble risk, updated unified verdict |
| `POST` | `/api/analyze/data` | Descriptive stats, returns distribution, VaR, Sortino, Beta, drawdowns, OHLCV table |

### Market Intelligence

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `GET` | `/api/market/overview` | Major indices, sector heatmap, Fear & Greed index |
| `GET` | `/api/recommendations` | AI-scored top stock picks from curated watchlist |
| `GET` | `/api/sentiment/{symbol}` | Tavily news search → Groq LLM sentiment analysis |
| `GET` | `/api/fundamentals/{symbol}` | Valuation, profitability, health, targets, dividends |

### Tools

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `GET` | `/api/screener` | Multi-criteria stock screener (sector, price, RSI, signal filters) |
| `POST` | `/api/compare` | Side-by-side comparison with normalized returns & correlation matrix |

### Auth & Admin

| Method | Endpoint | Description |
|:------:|:---------|:------------|
| `POST` | `/api/auth/login` | Email/password login → JWT token |
| `POST` | `/api/auth/signup` | User registration |
| `GET` | `/api/auth/me` | Verify token, return user info |
| `GET` | `/api/admin/accuracy` | Prediction accuracy stats (admin only) |
| `POST` | `/api/admin/validate` | Trigger pending prediction validation |

### Sample Request / Response

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1mo", "interval": "1d"}'
```

<details>
<summary><b>📤 Response Structure (click to expand)</b></summary>

```json
{
  "symbol": "AAPL",
  "info": { "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics" },
  "current_price": 198.45,
  "price_change": 1.23,
  "signals": {
    "overall": "Buy",
    "score": 2,
    "macd": "Bullish",
    "rsi": { "value": 58.42, "signal": "Neutral" },
    "bollinger": "Neutral",
    "volume": "Above Average",
    "mfi": 62.15
  },
  "expert_risk": {
    "score": 45.0,
    "class": "MEDIUM",
    "factors": ["RSI Neutral at 58.4", "Bullish MACD (0.85)", "..."]
  },
  "unified_verdict": {
    "direction": "Bullish",
    "verdict_label": "Slightly Bullish",
    "score": 12.5,
    "confidence": 62.3,
    "explanation": ["Technical indicators are neutral — no strong directional signal"],
    "components": {
      "technical": { "score": 50.0, "weight": 100.0, "direction": "Bullish" }
    },
    "risk_summary": { "score": 45.0, "class": "MEDIUM", "factors": ["..."] }
  },
  "chart_data": [{ "time": 1712000000, "open": 195.0, "high": 199.0, "low": 194.5, "close": 198.45, "volume": 52000000 }],
  "indicator_data": [{ "time": 1712000000, "RSI": 58.42, "MACD": 0.85, "BB_upper": 205.0, "BB_middle": 197.0, "BB_lower": 189.0, "OBV": 1250000 }],
  "performance": { "volatility": 24.5, "sharpe_ratio": 1.2, "max_drawdown": -8.5 },
  "support_resistance": { "pivot": 197.3, "r1": 200.1, "s1": 194.5 }
}
```

</details>

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)
- API keys for [Groq](https://console.groq.com) and [Tavily](https://tavily.com) (both have free tiers)

### 1. Clone & Install

```bash
git clone https://github.com/ritikpandey01/stockpulse.git
cd stockpulse/backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GROQ_API_KEY=gsk_your_groq_key
TAVILY_API_KEY=tvly-your_tavily_key
ADMIN_EMAILS=your-email@example.com
```

### 3. Set Up Database

Run `supabase_schema.sql` (found in the `backend/` folder) in your Supabase SQL Editor to create:
- `predictions` — stores ML predictions for accuracy tracking
- `search_history` — logs user analysis history

### 4. Launch

```bash
# Assuming you are already in the backend folder
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** — the backend serves the frontend automatically.

> **Note:** The platform works without Supabase/Groq/Tavily credentials — auth, sentiment, and prediction tracking features will gracefully degrade while all core analysis features remain fully functional.

---

## 🧪 How We Built It

### Development Journey

<table>
<tr>
<td width="60"><b>Phase</b></td>
<td><b>What We Did</b></td>
</tr>
<tr>
<td align="center">1️⃣</td>
<td><b>Core Data Pipeline</b> — Built <code>market_data.py</code> for yfinance integration and <code>technical.py</code> with 20+ indicator calculations (RSI, MACD, Bollinger Bands, ATR, MFI, OBV, moving averages, pivot points). Implemented signal generation with a composite scoring system (-4 to +4).</td>
</tr>
<tr>
<td align="center">2️⃣</td>
<td><b>ML Prediction Engine</b> — Created <code>predictor.py</code> with an auto-selection pipeline: 6 regression models are trained on 12 engineered features, the best is selected via <code>GridSearchCV</code> with <code>TimeSeriesSplit</code> cross-validation. Added a separate 6-model ensemble for risk scoring that combines price direction, volatility, and RSI-based risk components.</td>
</tr>
<tr>
<td align="center">3️⃣</td>
<td><b>The Conflict Problem</b> — Technical signals would say "Buy" while ML predicted a drop. We realized separate tabs showing contradictory information was confusing. This led to the creation of the <b>Unified Analysis Engine</b>.</td>
</tr>
<tr>
<td align="center">4️⃣</td>
<td><b>Unified Analyzer</b> — Built <code>unified_analyzer.py</code> with normalization functions for each source, weighted aggregation with dynamic weight redistribution, confidence scoring based on inter-component agreement, and human-readable conflict explanations.</td>
</tr>
<tr>
<td align="center">5️⃣</td>
<td><b>Progressive Loading</b> — Split the analysis endpoint into 3 phases: instant rule-based signals (Phase 1), async ML training (Phase 2), and async sentiment (Phase 3). The frontend verdict card live-updates as each phase completes.</td>
</tr>
<tr>
<td align="center">6️⃣</td>
<td><b>Dashboard from 8→5 Tabs</b> — Consolidated a sprawling 8-tab interface into a focused 5-tab design. Merged Risk into Prediction tab, eliminated redundancy, added lazy loading for Fundamentals and Data tabs.</td>
</tr>
<tr>
<td align="center">7️⃣</td>
<td><b>Market Intelligence Layer</b> — Added Fear & Greed Index (VIX + S&P momentum + sector breadth), sector heatmap with 11 ETFs, AI-scored top picks from a 30-stock watchlist, and a 60-stock screener universe.</td>
</tr>
<tr>
<td align="center">8️⃣</td>
<td><b>Advanced Analytics</b> — Implemented Value at Risk (95%/99%), Sortino ratio, Calmar ratio, Beta vs S&P 500, volatility cones (5d/10d/21d/63d), drawdown time series, returns distribution with skewness/kurtosis.</td>
</tr>
<tr>
<td align="center">9️⃣</td>
<td><b>Prediction Accountability</b> — Every ML prediction is logged to Supabase with a <code>check_at</code> timestamp. A validation endpoint compares predicted vs actual prices and tracks win/loss rates by timeframe. Admin dashboard visualizes accuracy.</td>
</tr>
</table>

### Key Design Decisions

| Decision | Rationale |
|:---------|:----------|
| **Vanilla JS over React/Vue** | Zero build step, instant load times, full control over the DOM for chart integration |
| **Progressive analysis over single endpoint** | Users see results in <1s instead of waiting 10-15s for ML training |
| **Weighted consensus over simple voting** | A 3-1 vote doesn't capture that a strong ML prediction should matter more than a weak RSI signal |
| **Dynamic weight redistribution** | When sentiment data is unavailable, its 15% weight redistributes proportionally to the remaining sources |
| **Expert + Ensemble dual risk** | Rule-based risk catches known patterns (RSI overbought + resistance), ensemble risk captures statistical patterns humans miss |

---

## 📈 Future Roadmap

- [ ] **Extended Asset Classes** — Forex, crypto, commodities support
- [ ] **Real-Time WebSocket Streaming** — Live price updates without polling
- [ ] **Visual Backtesting Engine** — Test strategies against historical data
- [ ] **Portfolio Tracker** — Multi-asset portfolio with aggregate risk/return
- [ ] **XGBoost + CatBoost Integration** — Currently commented out, ready for activation
- [ ] **Institutional Risk Dashboard** — Drawdown tracking, auto-balancing alerts

---

<p align="center">
  <sub>Built with ⚡ by <a href="https://github.com/ritikpandey01">Ritik Pandey</a></sub><br>
  <sub><i>Make data-driven decisions with unshakeable confidence.</i></sub>
</p>
