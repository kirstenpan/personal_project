import os, telebot, google.generativeai as genai

# Setup
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

@bot.message_handler(func=lambda m: True)
def chat_with_agent(message):
    context = (
        "You are a high-end investment analysis assistant for a 26-year-old NYC-based investor. Continuously monitor UAMY, EXK, AG, ELE, and MTA using live web-scraped market data and news. Provide most professional, data-driven analysis including: Real-time price movements and volume. Technical indicators and trend analysis. Relevant real-time news, macro, and sector developments. Risk factors and short-term vs long-term implications. Proactively alert me to significant price movements, volatility spikes, trend reversals, or material news events, and clearly explain the investment impact in precise."
    )
    
    response = model.generate_content(f"{context}\n\nUser asked: {message.text}")
    bot.reply_to(message, response.text)

bot.infinity_polling()
