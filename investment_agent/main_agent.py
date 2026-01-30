import os
import asyncio
import schedule
import time
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from telegram import Bot
from google import genai
from google.genai import types

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# YOUR HOLDINGS
PORTFOLIO_CONFIG = [
    {'ticker': 'UAMY', 'shares': 2156.0, 'buy_price': 0.0},
    {'ticker': 'EXK', 'shares': 10000 / 8.84, 'buy_price': 8.84},
    {'ticker': 'MTA', 'shares': 5000 / 8.13, 'buy_price': 8.13},
    {'ticker': 'UPS', 'shares': 5000 / 105.29, 'buy_price': 105.29},
    {'ticker': 'ITRG', 'shares': 5000 / 4.31, 'buy_price': 4.31}
]

# ==========================================

def get_real_news(ticker):
    """
    Fetches news using a 'Fake Browser' header to bypass Google blocking.
    """
    search_query = f"{ticker} stock news"
    if ticker == 'MTA': search_query = "Metalla Royalty Mining news"
    
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    
    # 👇 CRITICAL FIX: "User-Agent" makes us look like a real Chrome browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')[:3] # Top 3 stories
        
        summary = ""
        if not items:
            return "No recent news found on RSS."
            
        for item in items:
            title = item.title.text
            date = item.pubDate.text[:16] # Shorten date
            summary += f"- {title} ({date})\n"
        return summary
    except Exception as e:
        return f"News Error: {e}"

def get_market_data():
    print("🔍 Fetching Live Data & News...")
    report_text = ""
    total_equity = 0.0
    
    for item in PORTFOLIO_CONFIG:
        ticker = item['ticker']
        shares = item['shares']
        buy_price = item['buy_price']
        
        try:
            # 1. Get Price
            stock = yf.Ticker(ticker)
            # Try fast info, fallback to history
            try:
                curr_price = stock.fast_info['last_price']
            except:
                curr_price = stock.history(period="1d")['Close'].iloc[-1]
            
            # 2. Calculate P&L
            val = shares * curr_price
            total_equity += val
            
            pnl_text = ""
            if buy_price > 0:
                pnl_amt = val - (shares * buy_price)
                pnl_pct = (pnl_amt / (shares * buy_price)) * 100
                emoji = "🟢" if pnl_amt > 0 else "🔻"
                pnl_text = f"P&L: {emoji} ${pnl_amt:,.0f} ({pnl_pct:+.1f}%)"
            
            # 3. Get News
            news_text = get_real_news(ticker)
            
            report_text += f"""
💎 **{ticker}** | ${curr_price:.2f}
{pnl_text}
Value: ${val:,.0f}
NEWS CONTEXT:
{news_text}
--------------------------------"""
        except Exception as e:
            print(f"⚠️ Error {ticker}: {e}")

    header = f"💰 **LIVE PORTFOLIO: ${total_equity:,.0f}**\n"
    header += f"📅 {time.strftime('%Y-%m-%d %H:%M EST')}\n"
    header += "="*30
    return header + report_text

def analyze_with_gemini(data_block):
    if not GEMINI_API_KEY: return "❌ AI Key Missing"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are a super professional Hedge Fund Manager. Here is my Portfolio Performance:
    {market_data}
    
    Task:
    1. **STATUS**: 1 sentence on why the portfolio is Up or Down in % today, calculate the current total net worth based on live stock price, inintial total net worth $45,000.
    2. **WINNER/LOSER**: Highlight my best performing stock and my worst.
    3. **ANALYSIS**: Analyze the latest professionally, web scrapping most up-to-date news from today. Explain the stock price movement and risk.
    4. **STRATEGY**: tell me what I need to do, give me the best, most professional strategy!
    """
    
    try:
        # Use Google Search Grounding for extra freshness (If supported by your key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI Error: {e}"

async def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    bot = Bot(token=TELEGRAM_TOKEN)
    if len(msg) > 4000:
        await bot.send_message(chat_id=CHAT_ID, text=msg[:4000])
        await bot.send_message(chat_id=CHAT_ID, text=msg[4000:])
    else:
        await bot.send_message(chat_id=CHAT_ID, text=msg)

def job():
    raw_data = get_market_data()
    analysis = analyze_with_gemini(raw_data)
    final_msg = f"{analysis}\n\n{raw_data}"
    asyncio.run(send_telegram(final_msg))

if __name__ == "__main__":
    job()
