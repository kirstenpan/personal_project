import os, requests, google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def get_market_intelligence():
    # 模拟 Web Scrapping 监控点
    # 监控 1: 上海银价溢价 (Shanghai Premium)
    shanghai_premium = 17.5 # 目前约为 $14-$17 [3, 4]
    # 监控 2: UAMY 政策进展
    doe_funding_status = "Pending $44M Application" # [5, 6]
    
    analysis_prompt = f"""
    Analyze the following data：
    1. 上海银价溢价: ${shanghai_premium} (当前西方正在挤兑实物) 
    2. UAMY 状态: {doe_funding_status} [5]
    3. EXK, MTA and AG status
    3. MTA 挂单目标: $8.10 [Image 16]
    Please send a sharp and highly professional investment instruction to mobile phone users with all your webscrapping information.
    """
    
    response = model.generate_content(analysis_prompt)
    send_to_telegram(response.text)

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "HTML" 
    }
    
    response = requests.post(url, data=payload)
    print(f"Telegram Status: {response.status_code}")
    print(f"Telegram Response: {response.text}")

get_market_intelligence()
