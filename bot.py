import logging
import requests
import asyncio
import random
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---------------- CONFIGURATION ---------------- #
BOT_TOKEN = "8451758265:AAEHvLJ_BsfxjQ1v7tihWzb-thzvhnA5Hs0"
ACCESS_PASSWORD = "robin1235"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
# ----------------------------------------------- #

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER (Render Fix) ---
class SimpleHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Wingo Bot Running with Auto-Proxy')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTP)
    server.serve_forever()

def start_dummy_server():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

# --- PROXY SCRAPER (নতুন ফিচার) ---
def get_fresh_proxies():
    """ইন্টারনেট থেকে অটোমেটিক সচল প্রক্সি খুঁজে বের করবে"""
    try:
        # GitHub থেকে হাজার হাজার ফ্রি প্রক্সি লিস্ট নামাবে
        url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            return [p.strip() for p in proxies if p.strip()]
    except:
        pass
    return []

# --- ASSETS ---
BANNER = """
<pre>
██╗    ██╗██╗███╗   ██╗ ██████╗  ██████╗ 
██║    ██║██║████╗  ██║██╔════╝ ██╔═══██╗
██║ █╗ ██║██║██╔██╗ ██║██║  ███╗██║   ██║
██║███╗██║██║██║╚██╗██║██║   ██║██║   ██║
╚███╔███╔╝██║██║ ╚████║╚██████╔╝╚██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ 
</pre>
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data.clear()
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    login_msg = (
        f"{BANNER}"
        "<b>🔒 SYSTEM LOCKED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <b>SECURITY:</b> <code>AUTO-PROXY ROTATION</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 <b>ENTER ACCESS PASSWORD:</b>"
    )
    await update.message.reply_text(login_msg, parse_mode=ParseMode.HTML)

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id

    if context.user_data.get('logged_in'):
        return

    if user_msg == ACCESS_PASSWORD:
        context.user_data['logged_in'] = True
        context.user_data['wins'] = 0
        context.user_data['losses'] = 0
        context.user_data['last_period'] = None
        
        await update.message.reply_html(f"✅ <b>ACCESS GRANTED!</b>\n🌍 <b>SEARCHING FOR WORKING PROXIES...</b>\n(This might take few seconds)")
        
        # লুপ চালু
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id, name=str(chat_id))
    else:
        await update.message.reply_text("❌ Wrong Password!")

def fetch_data_with_proxy():
    """স্মার্ট প্রক্সি সিস্টেম"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.ar-lottery01.com/'
    }
    params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}

    # ১. প্রথমে ডাইরেক্ট চেষ্টা (যদি ভাগ্য ভালো থাকে)
    try:
        res = requests.get(API_URL, headers=headers, params=params, timeout=3)
        if res.status_code == 200:
            return res.json()['data']['list']
    except:
        pass

    # ২. ডাইরেক্ট ফেইল হলে নতুন প্রক্সি ডাউনলোড করবে
    proxy_list = get_fresh_proxies()
    
    if not proxy_list:
        return None

    # ৩. র‍্যান্ডম প্রক্সি দিয়ে ১০ বার চেষ্টা করবে
    for _ in range(10):
        try:
            proxy = random.choice(proxy_list)
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            
            # প্রক্সি দিয়ে রিকোয়েস্ট (টাইমআউট ৩ সেকেন্ড যাতে ফাস্ট হয়)
            res = requests.get(API_URL, headers=headers, params=params, proxies=proxies, timeout=3)
            
            if res.status_code == 200:
                data = res.json()
                if data['code'] == 0:
                    return data['data']['list']
        except:
            continue # ফেইল হলে পরের প্রক্সি ট্রাই করবে

    return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_data = context.application.user_data[job.user_id]
    
    if not user_data.get('logged_in'):
        job.schedule_removal()
        return

    history = fetch_data_with_proxy()
    
    # কানেকশন না পেলে চুপ থাকবে (বারবার এরর দেখাবে না)
    if not history: 
        return

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # WIN/LOSS CHECK
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            res_msg = f"✅ <b>WIN!</b> {real_res} 💰"
        else:
            user_data['losses'] += 1
            res_msg = f"❌ <b>LOSS!</b> {real_res} 💀"
        
        await context.bot.send_message(chat_id=chat_id, text=res_msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # NEW SIGNAL
    if last_period_saved != next_period:
        results = ["BIG" if int(x['number']) >= 5 else "SMALL" for x in history[:10]]
        l1, l2, l3 = results[0], results[1], results[2]

        if l2 == l3 and l1 != l2:
            pred, h_type = l1, "AABB 🧬"
        elif l1 == l2:
            pred, h_type = l1, "DRAGON 🐉"
        else:
            pred, h_type = ("SMALL" if l1 == "BIG" else "BIG"), "FLIP ⚡"

        user_data['last_period'] = next_period
        user_data['last_prediction'] = pred
        
        stream = " ".join(["B" if int(x['number']) >= 5 else "S" for x in history[:8]])
        
        msg = (
            f"🎯 <b>Target:</b> <code>{next_period}</code>\n"
            f"🦠 <b>Type:</b> {h_type}\n"
            f"🔮 <b>Predict:</b> <b>{pred}</b>\n"
            f"📡 {stream}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    start_dummy_server()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))
    application.run_polling()
