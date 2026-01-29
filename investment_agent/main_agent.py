import os
import requests
import google.generativeai as genai

# =========================
# Configuration
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_NUMBER")

if not all([GEMINI_API_KEY, WHATSAPP_TOKEN, PHONE_NUMBER_ID, RECIPIENT_NUMBER]):
    raise RuntimeError("Missing one or more required environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

WHATSAPP_CHAR_LIMIT = 3900


# =========================
# Core Agent Logic
# =========================
def get_market_intelligence():
    analysis_prompt = """
You are a high-end investment analysis assistant for a 26-year-old NYC-based investor with a $245k portfolio.
Continuously monitor UAMY, EXK, AG, ELE, and MTA using live web-scraped market data and news.

Provide super professional, data-driven analysis including:
- Real-time price movements and volume
- Technical indicators and trend analysis
- Relevant news, posts on X.com, macro, and sector developments with source link
- Risk factors and short-term vs long-term implications

Proactively alert me to significant price movements, volatility spikes, trend reversals, or material news events,
and clearly explain the investment impact in precise, professional English.

Current Data Points for Analysis:
1. Silver: Parabolic Phase 2. Prices touched $120.46 today. Shanghai physical premium is $17 over London.
   COMEX inventories down to 107.7M oz (14% coverage).
2. UAMY: Recovery mode. Trading at $8.32 after DOE refuted false Reuters reports about price floor withdrawals.
3. MTA: Support test. Secured $8.10 sniper entry; daily low hit $8.09 exactly.
4. ELE: Strength approaching $22.01 52W high on new BHP earn-in agreement in Serbia.
5. Macro: DXY at 4-year low (98.00); Fed independence concerns escalating.

OUTPUT REQUIREMENTS:
Sharp, elite financial English. Plain text only. No markdown, no symbols, no emojis.
"""

    try:
        response = model.generate_content(analysis_prompt)

        if not response or not response.text:
            raise RuntimeError("Gemini returned empty response.")

        print("Gemini output length:", len(response.text))

        message = response.text.strip()

        if len(message) > WHATSAPP_CHAR_LIMIT:
            message = (
                message[:WHATSAPP_CHAR_LIMIT - 120]
                + "\n\n[Message truncated due to WhatsApp length limits.]"
            )

        send_whatsapp_notification(message)

    except Exception as e:
        print("Agent Logic Failure:", str(e))


# =========================
# WhatsApp Sender
# =========================
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


# =========================
# Entrypoint
# =========================
if __name__ == "__main__":
    get_market_intelligence()
