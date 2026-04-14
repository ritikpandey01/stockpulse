import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def get_fundamentals(symbol: str) -> dict:
    """Fetch comprehensive fundamental data for a stock symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Core metrics
        core = {
            "name": info.get("shortName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", "")[:500],
            "employees": info.get("fullTimeEmployees", None),
        }

        # Valuation metrics
        valuation = {
            "market_cap": info.get("marketCap", None),
            "enterprise_value": info.get("enterpriseValue", None),
            "pe_trailing": info.get("trailingPE", None),
            "pe_forward": info.get("forwardPE", None),
            "peg_ratio": info.get("pegRatio", None),
            "ps_ratio": info.get("priceToSalesTrailing12Months", None),
            "pb_ratio": info.get("priceToBook", None),
            "ev_ebitda": info.get("enterpriseToEbitda", None),
        }

        # Profitability
        profitability = {
            "revenue": info.get("totalRevenue", None),
            "revenue_growth": _pct(info.get("revenueGrowth")),
            "gross_margins": _pct(info.get("grossMargins")),
            "operating_margins": _pct(info.get("operatingMargins")),
            "profit_margins": _pct(info.get("profitMargins")),
            "eps_trailing": info.get("trailingEps", None),
            "eps_forward": info.get("forwardEps", None),
            "roe": _pct(info.get("returnOnEquity")),
            "roa": _pct(info.get("returnOnAssets")),
        }

        # Dividends
        dividends = {
            "dividend_rate": info.get("dividendRate", None),
            "dividend_yield": _pct(info.get("dividendYield")),
            "payout_ratio": _pct(info.get("payoutRatio")),
            "ex_dividend_date": info.get("exDividendDate", None),
        }

        # Price targets
        targets = {
            "target_high": info.get("targetHighPrice", None),
            "target_low": info.get("targetLowPrice", None),
            "target_mean": info.get("targetMeanPrice", None),
            "target_median": info.get("targetMedianPrice", None),
            "recommendation": info.get("recommendationKey", "N/A"),
            "num_analysts": info.get("numberOfAnalystOpinions", 0),
        }

        # Financial health
        financial_health = {
            "total_cash": info.get("totalCash", None),
            "total_debt": info.get("totalDebt", None),
            "debt_to_equity": info.get("debtToEquity", None),
            "current_ratio": info.get("currentRatio", None),
            "free_cashflow": info.get("freeCashflow", None),
            "operating_cashflow": info.get("operatingCashflow", None),
        }

        # 52-week range
        price_info = {
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "50d_avg": info.get("fiftyDayAverage", None),
            "200d_avg": info.get("twoHundredDayAverage", None),
            "avg_volume": info.get("averageVolume", None),
            "avg_volume_10d": info.get("averageDailyVolume10Day", None),
        }

        return {
            "symbol": symbol,
            "core": core,
            "valuation": valuation,
            "profitability": profitability,
            "dividends": dividends,
            "targets": targets,
            "financial_health": financial_health,
            "price_info": price_info,
        }

    except Exception as e:
        logger.error(f"Fundamentals error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def _pct(val):
    """Convert decimal to percentage if not None."""
    if val is None:
        return None
    return round(float(val) * 100, 2)
