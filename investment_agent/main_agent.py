import os
import asyncio
import time
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from telegram import Bot
from google import genai
from datetime import datetime, timezone, timedelta

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PORTFOLIO_CONFIG = [
    {'ticker': 'UAMY', 'shares': 2156.0, 'buy_price': 9.28},
    {'ticker': 'EXK', 'shares': 1131.0, 'buy_price': 8.84},
    {'ticker': 'MTA', 'shares': 614.0, 'buy_price': 8.13},
    {'ticker': 'UPS', 'shares': 47.0, 'buy_price': 105.29},
    {'ticker': 'ITRG', 'shares': 1160.0, 'buy_price': 4.31}
]

# ==========================================

def get_real_news(ticker):
    """
    Robust Scraper: Uses 'html.parser' to avoid XML errors.
    """
    search_query = f"{ticker} stock news"
    if ticker == 'MTA': search_query = "Metalla Royalty Mining news"
    
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, features="html.parser")
        items = soup.find_all('item')[:3]
        
        summary = ""
        if not items:
            return "• No recent news found."
            
        for item in items:
            title_tag = item.find('title')
            date_tag = item.find('pubdate')
            
            title = title_tag.get_text() if title_tag else "No Title"
            date = date_tag.get_text()[:16] if date_tag else ""
            
            summary += f"• {title} ({date})\n"
        return summary
    except Exception as e:
        return f"• (News Error: {e})"

def get_market_data():
    print("🔍 Fetching Data...")
    
    # Check Market Status (EST Time)
    est_offset = timezone(timedelta(hours=-5))
    now = datetime.now(est_offset)
    is_open = (now.weekday() < 5) and (9 <= now.hour < 16)
    status_emoji = "🟢" if is_open else "zzz"
    status_text = "MARKET OPEN" if is_open else "MARKET CLOSED"
    
    report_text = ""
    total_equity = 0.0
    
    for item in PORTFOLIO_CONFIG:
        ticker = item['ticker']
        shares = item['shares']
        buy_price = item['buy_price']
        
        try:
            stock = yf.Ticker(ticker)
            try:
                curr_price = stock.fast_info['last_price']
            except:
                curr_price = stock.history(period="1d")['Close'].iloc[-1]
            
            if curr_price is None: curr_price = 0.0

            val = shares * curr_price
            total_equity += val
            
            pnl_text = ""
            if buy_price > 0 and curr_price > 0:
                pnl_amt = val - (shares * buy_price)
                pnl_pct = (pnl_amt / (shares * buy_price)) * 100
                emoji = "🟢" if pnl_amt > 0 else "🔻"
                pnl_text = f"P&L: {emoji} ${pnl_amt:,.0f} ({pnl_pct:+.1f}%)"
            
            news_text = get_real_news(ticker)
            
            report_text += f"""
💎 **{ticker}** | ${curr_price:.2f}
{pnl_text}
Value: ${val:,.0f}
NEWS:
{news_text}
--------------------------------"""
        except Exception as e:
            print(f"⚠️ Error {ticker}: {e}")

    header = f"💰 **LIVE PORTFOLIO: ${total_equity:,.0f}**\n"
    header += f"📅 {now.strftime('%Y-%m-%d %H:%M EST')} | {status_emoji} {status_text}\n"
    header += "="*30
    return header + report_text

def analyze_with_gemini(data_block):
    if not GEMINI_API_KEY: return "❌ AI Key Missing"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 👇 YOUR EXACT PROMPT (No Changes)
    prompt = f"""
    You are a super professional Hedge Fund Manager. Here is my Portfolio Performance (do not tell me any disclaimer because I know already):
    {data_block}
    
    Task:
    1. **STATUS**: 1 sentence on why the portfolio is Up or Down in % today, calculate the current total net worth based on live stock price, inintial total net worth $45,000.
    2. **WINNER/LOSER**: Highlight my best performing stock and my worst.
    3. **ANALYSIS**: Analyze the latest professionally, web scrapping most up-to-date news from today. Explain the stock price movement and risk.
    4. **STRATEGY**: tell me what I need to do, give me the best, most professional strategy!
    """
    
    try:
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
