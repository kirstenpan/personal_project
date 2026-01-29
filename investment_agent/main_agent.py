import os
import requests
from datetime import datetime
import yfinance as yf
import google.generativeai as genai

# =====================================================
# ENV CONFIG
# =====================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_NUMBER")

if not all([GEMINI_API_KEY, WHATSAPP_TOKEN, PHONE_NUMBER_ID, RECIPIENT_NUMBER]):
    raise RuntimeError("Missing required environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

WHATSAPP_CHAR_LIMIT = 3900

# =====================================================
# REAL-TIME MARKET DATA FETCH
# =====================================================
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

    market_data = {}

    for name, ticker in tickers.items():
        t = yf.Ticker(ticker)
        info = t.fast_info

        market_data[name] = {
            "price": info.get("lastPrice"),
            "prev_close": info.get("previousClose"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "volume": info.get("volume")
        }

    return market_data

# =====================================================
# PROMPT BUILDER (FACT-IN → ANALYSIS-OUT)
# =====================================================
def build_analysis_prompt(market_data):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""
You are a senior investment analyst advising a 26-year-old NYC-based investor with a $245k portfolio.

Live market snapshot as of {timestamp} (real data, not hypothetical):

{market_data}

Analyze with institutional rigor.

Focus on:
- Momentum and intraday trend quality
- Support/resistance implications
- Volume confirmation or divergence
- Silver vs miners relationship
- DXY impact on metals and equities
- Short-term risk vs opportunity
- What matters over the next 24–72 hours

Output rules:
Plain professional English.
No markdown.
No emojis.
No symbols.
Concise, decisive, and actionable.
"""

# =====================================================
# WHATSAPP SENDER
# =====================================================
def send_whatsapp_notification(message: str):
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

    response = requests.post(url, headers=headers, json=payload)

    print("WhatsApp status:", response.status_code)
    print("WhatsApp response:", response.text)

# =====================================================
# CORE AGENT LOOP
# =====================================================
def get_market_intelligence():
    try:
        market_data = fetch_market_data()
        print("Fetched live market data:", market_data)

        prompt = build_analysis_prompt(market_data)
        response = model.generate_content(prompt)

        if not response or not response.text:
            raise RuntimeError("Empty Gemini response")

        message = response.text.strip()
        print("Gemini output length:", len(message))

        if len(message) > WHATSAPP_CHAR_LIMIT:
            message = (
                message[:WHATSAPP_CHAR_LIMIT - 120]
                + "\n\n[Message truncated due to WhatsApp limits]"
            )

        send_whatsapp_notification(message)

    except Exception as e:
        print("Agent failure:", str(e))

# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    get_market_intelligence()
