import os
import requests
import google.generativeai as genai
import yfinance as yf
import snscrape.modules.twitter as sntwitter
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

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

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
# X (TWITTER) SCRAPING
# =========================
def fetch_x_sentiment():
    queries = [
        "silver market",
        "COMEX silver",
        "UAMY stock",
        "AG silver stock",
        "EXK mining",
        "Federal Reserve independence"
    ]

    tweets = []

    for q in queries:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(q).get_items()):
            if i >= 3:
                break
            tweets.append(f"{tweet.date.date()} | {q} | {tweet.content}")

    return tweets

# =========================
# PROMPT BUILDER
# =========================
def build_prompt(market_data, tweets):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""
You are a super professional buy-side investment analyst.

Timestamp: {now}

LIVE MARKET DATA:
{market_data}

RECENT X (TWITTER) SIGNALS:
{tweets}

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
        tweets = fetch_x_sentiment()

        print("Market data fetched")
        print("Tweets fetched:", len(tweets))

        prompt = build_prompt(market_data, tweets)
        response = model.generate_content(prompt)

        if not response or not response.text:
            raise RuntimeError("Gemini returned empty response")

        msg = response.text.strip()

        if len(msg) > WHATSAPP_LIMIT:
            msg = msg[:3800] + "\n\n[Truncated]"

        send_whatsapp(msg)

    except Exception as e:
        print("AGENT FAILURE:", str(e))

# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    run_agent()
