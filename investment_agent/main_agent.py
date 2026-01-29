import os, telebot, google.generativeai as genai

# Setup
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

@bot.message_handler(func=lambda m: True)
def chat_with_agent(message):
    # Context: You are a 26yo NYC investor with $245k portfolio
    # You just bought MTA at $8.10 [Image 16]
    context = (
        "You are the personal AI Agent for a 26-year-old Manhattan investor. "
        "Portfolio Context: $245k total net worth, 70 MSFT, 110 SPY, 2155 UAMY. "
        "Recent Trade: Bought 5k MTA at $8.10. "
        "Goal: $5M by age 37. Respond in sharp, professional English."
    )
    
    response = model.generate_content(f"{context}\n\nUser asked: {message.text}")
    bot.reply_to(message, response.text)

# This keeps the bot listening 24/7
bot.infinity_polling()
