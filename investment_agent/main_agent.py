import os, requests, google.generativeai as genai

# Configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def get_market_intelligence():
    # LIVE DATA FEED - January 29, 2026
    # Silver: $117.63 (ATH $120.46 today) | Shanghai Premium: $17
    # UAMY: $8.32 (V-bottom from $7.80) | MTA: $8.16 (Support at $8.09)
    # ELE: $21.72 (Approaching 52W High $22.01)
    
    analysis_prompt = """
    You are a high-end investment analysis assistant for a 26-year-old NYC-based investor with a $245k portfolio.
    Continuously monitor UAMY, EXK, AG, ELE, and MTA using live web-scraped market data and news.
    
    Provide super professional, data-driven analysis including:
    - Real-time price movements and volume
    - Technical indicators and trend analysis
    - Relevant news, post on X.com, macro, and sector developments with source link
    - Risk factors and short-term vs long-term implications
    
    Proactively alert me to significant price movements, volatility spikes, trend reversals, or material news events, and clearly explain the investment impact in precise, professional English.
    
    Current Data Points for Analysis:
    1. Silver: Parabolic Phase 2. Prices touched $120.46 today. Shanghai physical premium is $17 over London. COMEX inventories down to 107.7M oz (14% coverage).
    2. UAMY: Recovery mode. Trading at $8.32 after DOE refuted false Reuters reports about price floor withdrawals.
    3. MTA: Support test. Secured $8.10 sniper entry; daily low hit $8.09 exactly.
    4. ELE: Strength.approaching $22.01 52W high on new BHP earn-in agreement in Serbia.
    5. Macro: DXY at 4-year low (98.00); Fed independence concerns escalating.
    
    OUTPUT REQUIREMENTS: Sharp, elite financial English. Plain text only. No special symbols, no asterisks, no markdown.
    """
    
    try:
        response = model.generate_content(analysis_prompt)
        send_whatsapp_notification(response.text)
    except Exception as e:
        print(f"Agent Logic Failure: {e}")

def send_whatsapp_notification(message):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")
    to_number = os.getenv("RECIPIENT_NUMBER")
    
    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    get_market_intelligence()
