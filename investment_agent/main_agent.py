import os, requests, time, google.generativeai as genai

# Setup Gemini 2.0 Flash
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def get_market_intelligence():
    # Agent Intelligence Data Points (Jan 29, 2026)
    # 1. MSFT Beat: $81.3B Revenue, Azure growth at 40%
    # 2. UAMY Fact-Check: DOE calls Reuters report "false/misleading"
    # 3. Silver Squeeze: Shanghai premium at $17 [1]
    
    analysis_prompt = """
    You are a high-end investment assistant for a 26-year-old NYC investor with a $245k portfolio. 
    Analyze these 3 events in sharp, professional English:
    - Microsoft (MSFT) Q2 Results: $81.3B revenue, 40% Azure growth.
    - UAMY: DOE officially refuted the Reuters report about price floors.
    - Silver: Shanghai physical premium is $17 over NY/London.
    Provide a clear 'Actionable Intelligence' summary. 
    Use ONLY plain text. NO asterisks, NO underscores, NO markdown.
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
