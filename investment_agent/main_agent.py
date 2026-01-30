import os
import asyncio
import schedule
import time
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from telegram import Bot
from google import genai

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# 👇 CRITICAL FIX: Read keys from GitHub Secrets (Environment Variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Your Specific Holdings
PORTFOLIO = {
    'UAMY': 2156,
    'EXK': 1132,
    'MTA': 615,
    'UPS': 47,
    'ITRG': 1161
}
# ==========================================

# --- 1. INTELLIGENT NEWS SCRAPER ---
def get_news_and_social(ticker):
    """
    Scrapes Google News RSS for real-time headlines.
    """
    # 1. Google News RSS (Fast & Free)
    search_query = f"{ticker} stock news"
    if ticker == 'MTA': search_query = "Metalla Royalty news" # Fix for MTA subway confusion
    
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    
    news_summary = ""
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')[:3] # Get top 3 latest stories
        
        if not items:
            news_summary = "• No breaking news in last 24h."
        else:
            for item in items:
                news_summary += f"• {item.title.text} ({item.pubDate.text[:16]})\n"
    except Exception as e:
        news_summary = f"• (Error fetching news: {e})"

    return news_summary

# --- 2. LIVE MARKET DATA ENGINE ---
def get_market_snapshot():
    print("🔍 Scanning Market & News...")
    snapshot = ""
    total_portfolio_value = 0.0
    
    for ticker, shares in PORTFOLIO.items():
        try:
            # Fetch Live Data
            stock = yf.Ticker(ticker)
            # Handle potential missing data safely
            try:
                price = stock.fast_info['last_price']
                prev_close = stock.fast_info['previous_close']
            except:
                # Fallback if fast_info fails
                hist = stock.history(period="1d")
                price = hist['Close'].iloc[-1]
                prev_close = hist['Open'].iloc[-1]

            # Math
            change_pct = ((price - prev_close) / prev_close) * 100
            position_value = price * shares
            total_portfolio_value += position_value
            
            # Trend Emoji
            if change_pct > 1.0: trend = "🚀"
            elif change_pct > 0.0: trend = "🟢"
            elif change_pct < -1.0: trend = "🩸"
            else: trend = "🔴"
            
            # Get News
            news = get_news_and_social(ticker)
            
            # Build Report Section
            snapshot += f"""
{trend} **{ticker}**
   • Price: ${price:.2f} ({change_pct:+.2f}%)
   • My Value: ${position_value:,.2f}
   • News Logic:
     {news}
--------------------------------"""
        except Exception as e:
            print(f"⚠️ Error with {ticker}: {e}")

    # Add Total Summary at the top
    header = f"💰 **TOTAL PORTFOLIO: ${total_portfolio_value:,.2f}**\n"
    header += f"📅 Time: {time.strftime('%Y-%m-%d %H:%M EST')}\n"
    header += "="*30 + "\n"
    
    return header + snapshot

# --- 3. GEMINI 2.0 ANALYST BRAIN ---
def analyze_with_gemini(market_data):
    if not GEMINI_API_KEY:
        return "❌ Error: GEMINI_API_KEY not found in secrets."

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an elite Wall Street Hedge Fund Manager (Aggressive/Contrarian Style).
    I own these stocks. Here is the LIVE data and News:
    
    {market_data}
    
    Your Job:
    1. **TOTAL HEALTH**: One sentence on my total equity status.
    2. **DEEP DIVE**: Pick the most volatile stock right now. Explain WHY it is moving based on the news provided.
    3. **ACTION PLAN**: Give me a specific "BUY", "SELL", or "HOLD" for UAMY and EXK.
    4. **X.com VIRAL POST**: Write a short, punchy tweet I can copy-paste to X.com. It must sound like a professional trader. Use $CASH_TAGS.

    Output format: Clean text with emojis. No markdown code blocks.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ AI Analysis Failed: {e}"

# --- 4. TELEGRAM SENDER ---
async def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: Telegram keys not found.")
        return

    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        # Split message if too long (Telegram limit is 4096 chars)
        if len(message) > 4000:
            await bot.send_message(chat_id=CHAT_ID, text=message[:4000])
            await bot.send_message(chat_id=CHAT_ID, text=message[4000:])
        else:
            await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- 5. MAIN EXECUTION LOOP ---
def job():
    print("⏳ Starting Hourly Scan...")
    
    # Step 1: Get Data
    raw_data = get_market_snapshot()
    
    # Step 2: Analyze
    ai_report = analyze_with_gemini(raw_data)
    
    # Step 3: Send
    final_message = f"{ai_report}\n\n" + "="*20 + f"\n🔍 [Check X.com for $UAMY](https://x.com/search?q=%24UAMY&src=typed_query&f=live)"
    
    asyncio.run(send_telegram(final_message))
    print("✅ Hourly Report Sent!")

# --- SCHEDULER ---
if __name__ == "__main__":
    # GitHub Actions handles the scheduling for us.
    job()
