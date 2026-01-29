import os
import requests
import yfinance as yf
import feedparser
from datetime import datetime

# =========================
# ENV CONFIG
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_NUMBER")

if not all([GEMINI_API_KEY, WHATSAPP_TOKEN, PHONE_NUMBER_ID, RECIPIENT_NUMBER]):
    raise RuntimeError("Missing required environment variables")

client = genai.Client(api_key=GEMINI_API_KEY)

WHATSAPP_LIMIT = 3900

# =========================
# MARKET DATA
# =========================
def fetch_market_data():
    tickers = {
        "UAMY": "UAMY",
        "EXK": "EXK",
        "AG": "AG",
        "ELE": "ELE",
        "MTA": "MTA",
        "SILVER": "SI=F",
        "DXY": "DX-Y.NYB"
    }

    snapshot = {}

    for name, ticker in tickers.items():
        t = yf.Ticker(ticker)
        info = t.fast_info

        snapshot[name] = {
            "price": info.get("lastPrice"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "prev_close": info.get("previousClose"),
            "volume": info.get("volume")
        }

    return snapshot

# =========================
# NEWS / SENTIMENT (RSS)
# =========================
def fetch_market_news():
    feeds = [
        "https://feeds.reuters.com/reuters/commoditiesNews",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.mining.com/feed/"
    ]

    headlines = []

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            headlines.append(f"{entry.title} ({entry.link})")

    return headlines

# =========================
# PROMPT BUILDER
# =========================
def build_prompt(market_data, news):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""
You are a super professional buy-side investment analyst.

Timestamp: {now}

LIVE MARKET DATA:
{market_data}

RECENT X SIGNALS:
{x}

Analyze with institutional rigor.

gather all the useful information through research for me, including X.com, yfinance, etc. Focus on:
- Momentum, trend strength, stock price analysis, reason, and inflection risk
- Miner vs silver divergence or confirmation
- Volume confirmation or exhaustion
- Macro overlay (USD, Fed credibility)
- Short-term tactical risk and opportunity
- Whether alerts or action are warranted

Output rules:
Plain English only. Less than 3800 characters.
No markdown.
No emojis.
No symbols.
Concise but decisive.
"""

# =========================
# WHATSAPP
# =========================
def send_whatsapp(message):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_NUMBER,
        "type": "text",
        "text": {"body": message}
    }

    r = requests.post(url, headers=headers, json=payload)
    print("WhatsApp status:", r.status_code)
    print("WhatsApp response:", r.text)

# =========================
# AGENT
# =========================
def run_agent():
    try:
        market_data = fetch_market_data()
        news = fetch_market_news()

        prompt = build_prompt(market_data, news)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        if len(text) > WHATSAPP_LIMIT:
            text = text[:3800] + "\n\n[Truncated]"

        send_whatsapp(text)

    except Exception as e:
        send_whatsapp(f"Agent error: {str(e)}")

# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    run_agent()
