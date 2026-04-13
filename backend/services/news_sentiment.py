import logging
from config import TAVILY_API_KEY, GROQ_API_KEY

logger = logging.getLogger(__name__)


async def search_stock_news(symbol: str, company_name: str = "") -> list[dict]:
    """Search for recent news about a stock using Tavily."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        query = f"{symbol} {company_name} stock market news analysis latest"
        result = client.search(query=query, max_results=5, search_depth="basic")
        articles = []
        for r in result.get("results", []):
            articles.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],
            })
        return articles
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []


async def analyze_sentiment(symbol: str, articles: list[dict]) -> dict:
    """Use Groq LLM to analyze sentiment from news articles."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        if not articles:
            return {
                "mood": "Neutral",
                "score": 50,
                "confidence": 0,
                "summary": "No recent news found for analysis.",
                "key_factors": [],
            }

        news_text = "\n\n".join([
            f"**{a['title']}**\n{a['content']}" for a in articles
        ])

        prompt = f"""You are a senior financial analyst. Analyze the following news articles about stock ticker {symbol} and provide a sentiment analysis.

NEWS ARTICLES:
{news_text}

Respond ONLY with valid JSON in this exact format, no markdown, no extra text:
{{
  "mood": "Extreme Bullish" or "Bullish" or "Slightly Bullish" or "Neutral" or "Slightly Bearish" or "Bearish" or "Extreme Bearish",
  "score": <number from 0 to 100, where 0 is extreme fear and 100 is extreme greed>,
  "confidence": <number from 0 to 100>,
  "summary": "<2-3 sentence summary of the overall sentiment>",
  "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"]
}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        import json
        raw = response.choices[0].message.content.strip()
        # Try to extract JSON if wrapped in markdown
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
        return result

    except Exception as e:
        logger.error(f"Groq sentiment error: {e}")
        return {
            "mood": "Neutral",
            "score": 50,
            "confidence": 0,
            "summary": f"Sentiment analysis unavailable: {str(e)}",
            "key_factors": [],
        }


async def get_full_sentiment(symbol: str, company_name: str = "") -> dict:
    """Complete sentiment pipeline: search news then analyze."""
    articles = await search_stock_news(symbol, company_name)
    sentiment = await analyze_sentiment(symbol, articles)
    return {
        "sentiment": sentiment,
        "articles": articles,
    }
