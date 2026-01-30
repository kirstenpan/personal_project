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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 👇 UPDATED PORTFOLIO STRUCTURE
# We calculate shares dynamically based on your "Total Invested / Buy Price"
PORTFOLIO_CONFIG = [
    # UAMY: You own 2156 shares (Buy price unknown, set to 0 to track Total Value only)
    {'ticker': 'UAMY', 'shares': 2156.0, 'buy_price': 0.0},
    
    # EXK: $10,000 bought at $8.84
    {'ticker': 'EXK', 'shares': 10000 / 8.84, 'buy_price': 8.84},
    
    # MTA: $5,000 bought at $8.13
    {'ticker': 'MTA', 'shares': 5000 / 8.13, 'buy_price': 8.13},
    
    # UPS: $5,000 bought at $105.29
    {'ticker': 'UPS', 'shares': 5000 / 105.29, 'buy_price': 105.29},
    
    # ITRG: $5,000 bought at $4.31
    {'ticker': 'ITRG', 'shares': 5000 / 4.31, 'buy_price': 4.31}
]

# ==========================================

def get_news_and_social(ticker):
    """Scrapes Google News RSS for real-time headlines."""
    search_query = f"{ticker} stock news"
    if ticker == 'MTA': search_query = "Metalla Royalty news"
    
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    news_summary = ""
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')[:2] # Top 2 stories
        if not items: return "• No breaking news."
        for item in items:
            news_summary += f"• {item.title.text} ({item.pubDate.text[:16]})\n"
    except:
        return "• (News unavailable)"
    return news_summary

def get_market_snapshot():
    print("🔍 Scanning Market & Calculating P&L...")
    snapshot = ""
    total_equity = 0.0
    total_cost = 0.0
    
    for item in PORTFOLIO_CONFIG:
        ticker = item['ticker']
        shares = item['shares']
        buy_price = item['buy_price']
        
        try:
            # 1. Get Live Price
            stock = yf.Ticker(ticker)
            try:
                curr_price = stock.fast_info['last_price']
            except:
                curr_price = stock.history(period="1d")['Close'].iloc[-1]
            
            # 2. Calculate Math
            current_value = shares * curr_price
            initial_cost = shares * buy_price
            
            # Calculate Gain/Loss (if buy_price is known)
            if buy_price > 0:
                profit_dollar = current_value - initial_cost
                profit_pct = ((curr_price - buy_price) / buy_price) * 100
                total_cost += initial_cost
                
                # Emoji Logic
                if profit_pct > 0: pnl_str = f"🟢 +${profit_dollar:,.0f} (+{profit_pct:.1f}%)"
                else: pnl_str = f"🔻 -${abs(profit_dollar):,.0f} ({profit_pct:.1f}%)"
            else:
                pnl_str = "⚪ (Track Value Only)"
                # We don't add to total_cost if buy_price is 0 to avoid skewing "Total Performance"

            total_equity += current_value
            
            # 3. Get News
            news = get_news_and_social(ticker)
            
            snapshot += f"""
**{ticker}** | ${curr_price:.2f}
   • Val: ${current_value:,.0f} | Cost: ${buy_price:.2f}
   • P&L: {pnl_str}
   • News:
     {news}
--------------------------------"""
        except Exception as e:
            print(f"⚠️ Error {ticker}: {e}")
            snapshot += f"\n⚠️ {ticker}: Data Error\n"

    # Total Portfolio Summary
    total_pnl = total_equity - total_cost
    if total_cost > 0:
        total_pct = (total_pnl / total_cost) * 100
        header_emoji = "🚀" if total_pnl > 0 else "📉"
        header = f"{header_emoji} **NET WORTH: ${total_equity:,.0f}**\n"
        header += f"📊 Total Return: {total_pnl:+,.0f} ({total_pct:+.1f}%)\n"
    else:
        header = f"💰 **NET WORTH: ${total_equity:,.0f}**\n"
        
    header += f"📅 {time.strftime('%Y-%m-%d %H:%M EST')}\n" + "="*30 + "\n"
    return header + snapshot

def analyze_with_gemini(market_data):
    if not GEMINI_API_KEY: return "❌ Key Missing"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are a super professional Hedge Fund Manager. Here is my Portfolio Performance:
    {market_data}
    
    Task:
    1. **STATUS**: 1 sentence on why the portfolio is Up or Down today.
    2. **WINNER/LOSER**: Highlight my best performing stock and my worst.
    3. **ANALYSIS**: Analyze the latest professionally, web scrapping most up-to-date news from today. Explain the stock price movement and risk.
    4. **STRATEGY**: tell me what do I need to do, give me the best, most professional strategy!
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ AI Error: {e}"

async def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        if len(message) > 4000:
            await bot.send_message(chat_id=CHAT_ID, text=message[:4000])
            await bot.send_message(chat_id=CHAT_ID, text=message[4000:])
        else:
            await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Fail: {e}")

def job():
    data = get_market_snapshot()
    report = analyze_with_gemini(data)
    asyncio.run(send_telegram(f"{report}\n\n" + "="*20 + "\n" + data))

if __name__ == "__main__":
    job()
