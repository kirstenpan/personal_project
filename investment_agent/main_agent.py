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

# --- CONFIGURATION ---
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"
TELEGRAM_TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_TELEGRAM_CHAT_ID_HERE"

PORTFOLIO = {
    'UAMY': 2156,
    'EXK': 1132,
    'MTA': 615,
    'UPS': 47,
    'ITRG': 1161
}

# --- MODULE 1: INTELLIGENT NEWS SCRAPER ---
def get_news(ticker):
    # We refine the search query to avoid mistakes (e.g. MTA subway vs MTA stock)
    search_query = f"{ticker} stock news"
    if ticker == 'MTA':
        search_query = "Metalla Royalty stock news"
        
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll('item')[:2] # Top 2 stories only to save tokens
        news_text = ""
        for item in items:
            news_text += f"- {item.title.text} ({item.pubDate.text})\n"
        return news_text
    except:
        return "No recent news found."

# --- MODULE 2: MARKET DATA FETCH ---
def get_data():
    report_data = ""
    print("Fetching market data...")
    for ticker, shares in PORTFOLIO.items():
        try:
            # yfinance is free and reliable for delayed data
            stock = yf.Ticker(ticker)
            price = stock.fast_info['last_price']
            
            # Calculate value
            value = price * shares
            
            # Get News
            news = get_news(ticker)
            
            report_data += f"\n--- {ticker} ---\n"
            report_data += f"Price: ${price:.2f} | My Value: ${value:,.2f}\n"
            report_data += f"News:\n{news}\n"
        except Exception as e:
            print(f"Error on {ticker}: {e}")
            
    return report_data

# --- MODULE 3: GEMINI 2.0 FLASH BRAIN ---
def ask_gemini(market_data):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an elite hedge fund analyst. Analyze my portfolio based on this real-time data:
    {market_data}

    1. EXECUTIVE SUMMARY: One succinct sentence on my portfolio's status.
    2. ANALYSIS: For each stock, give a "BUY", "SELL", or "HOLD" recommendation based strictly on the news provided.
    3. X.com POST: Write a viral, professional tweet (max 280 chars) summarizing the biggest opportunity here. Use $TICKER tags.
    
    Format nicely with emojis.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

# --- MODULE 4: TELEGRAM SENDER ---
async def send_telegram(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    # Telegram has a char limit, Gemini can be verbose. We split if needed.
    if len(message) > 4000:
        await bot.send_message(chat_id=CHAT_ID, text=message[:4000])
        await bot.send_message(chat_id=CHAT_ID, text=message[4000:])
    else:
        await bot.send_message(chat_id=CHAT_ID, text=message)

# --- MAIN LOOP ---
def job():
    print("⏳ Starting scan cycle...")
    data = get_data()
    analysis = ask_gemini(data)
    
    final_msg = f"🤖 **GEMINI AGENT REPORT** 🤖\n{analysis}"
    
    asyncio.run(send_telegram(final_msg))
    print("✅ Report sent.")

# Schedule: Run every 1 hour
schedule.every(1).hours.do(job)

# Run once immediately on start to test
job()

while True:
    schedule.run_pending()
    time.sleep(1)
