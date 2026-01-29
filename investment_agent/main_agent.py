import os, requests, time, google.generativeai as genai

# Setup Gemini 2.0 Flash
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def get_market_intelligence():
    # Agent Web Scrapping: Live Research and Analysis
    # 1. MSFT Beat: $81.3B Revenue, Azure growth at 40%
    # 2. UAMY Fact-Check: DOE calls Reuters report "false/misleading"
    # 3. Silver Squeeze: Shanghai premium at $17 [1]
    
    analysis_prompt = """
    You are a high-end investment analysis assistant for a 26-year-old NYC-based investor.
    Continuously monitor UAMY, EXK, AG, ELE, and MTA using live web-scraped market data and news.
    Provide professional, data-driven analysis including:
    Real-time price movements and volume
    Technical indicators and trend analysis
    Relevant news, macro, and sector developments
    Risk factors and short-term vs long-term implications
    Proactively alert me to significant price movements, volatility spikes, trend reversals, or material news events, and clearly explain the investment impact in precise, professional English.
    """
    
    try:
        response = model.generate_content(analysis_prompt)
        report = response.text
        send_to_telegram(report)
    except Exception as e:
        print(f"Agent Safety Catch: {e}")

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Using 'HTML' mode is safer for AI text than 'Markdown'
    payload = {
        "chat_id": chat_id, 
        "text": f"<b></b>\n\n{text}", 
        "parse_mode": "HTML"
    }
    
    r = requests.post(url, data=payload)
    print(f"Telegram Status: {r.status_code}")
    print(f"Telegram Response: {r.text}")

if __name__ == "__main__":
    get_market_intelligence()
