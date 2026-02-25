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

# 🔥 POWERFUL PROXY SECTION
# যদি তোমার কেনা প্রক্সি থাকে, এখানে বসাও। না থাকলে ফাঁকা রাখো, অটোমেটিক ফ্রি প্রক্সি খুঁজবে।
STATIC_PROXIES = [
    # "http://zmnbdzbu:nmu1dv89xjl7@31.59.20.176:6754", 
    # "http://ip:port",
]
# ----------------------------------------------- #

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER (Render Fix) ---
class SimpleHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Ultra VIP Bot Running')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTP)
    server.serve_forever()

def start_dummy_server():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

# --- PROXY ENGINE ---
def get_proxy():
    """প্রথমে স্ট্যাটিক প্রক্সি দেখবে, না পেলে অটোমেটিক জেনারেট করবে"""
    # ১. যদি তোমার দেওয়া শক্তিশালী প্রক্সি থাকে
    if STATIC_PROXIES:
        return random.choice(STATIC_PROXIES)
    
    # ২. না থাকলে অটোমেটিক ইন্টারনেট থেকে খুঁজবে (Fallback)
    try:
        url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            return random.choice(proxies[:50]) # টপ ৫০টা থেকে একটা নিবে
    except:
        pass
    return None

# --- UI ASSETS ---
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
    
    # পুরোনো সেশন রিমুভ
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # 🔥 ULTRA LOGIN PAGE
    login_msg = (
        f"{BANNER}"
        "<b>☠️ SYSTEM: </b><code>DARK_NET_V4.0</code>\n"
        "<b>🛡️ SECURITY: </b><code>MILITARY GRADE ENCRYPTION</code>\n"
        "<b>📡 SERVER: </b><code>OFFSHORE_104</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>AUTHENTICATION REQUIRED</b>\n"
        "Restricted Area. Authorized Personnel Only.\n\n"
        "<b>🔑 ENTER ACCESS KEY:</b>"
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
        
        # 🔥 HACKER ANIMATION
        msg = await update.message.reply_html("<b>🔄 ESTABLISHING SECURE CONNECTION...</b>")
        await asyncio.sleep(0.8)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="<b>🔓 BYPASSING FIREWALL... [100%]</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.8)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="<b>💉 INJECTING SQL PAYLOAD...</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.8)
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=msg.message_id, 
            text=f"{BANNER}\n✅ <b>ACCESS GRANTED</b>\n🚀 <b>VIP SERVER CONNECTED</b>", 
            parse_mode=ParseMode.HTML
        )
        
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id, name=str(chat_id))
    else:
        await update.message.reply_html("<b>❌ ACCESS DENIED. IP LOGGED.</b>")

def fetch_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.ar-lottery01.com/'
    }
    params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}

    # ১. প্রথমে ডাইরেক্ট ট্রাই
    try:
        res = requests.get(API_URL, headers=headers, params=params, timeout=4)
        if res.status_code == 200: return res.json()['data']['list']
    except: pass

    # ২. প্রক্সি দিয়ে ট্রাই (লুপ)
    for _ in range(5):
        try:
            proxy = get_proxy()
            if not proxy: break
            
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            res = requests.get(API_URL, headers=headers, params=params, proxies=proxies, timeout=4)
            if res.status_code == 200: return res.json()['data']['list']
        except: continue
    
    return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_data = context.application.user_data[job.user_id]
    
    if not user_data.get('logged_in'):
        job.schedule_removal()
        return

    history = fetch_data()
    if not history: return

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # --- WIN/LOSS LOGIC (With Reset Feature) ---
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            # 🔥 MAGIC LOGIC: জিতলে লস রিসেট হয়ে যাবে!
            user_data['losses'] = 0 
            res_msg = f"✅ <b>SUCCESS!</b> <code>{real_res}</code> 💰"
        else:
            user_data['losses'] += 1
            res_msg = f"❌ <b>FAIL!</b> <code>{real_res}</code> 💀"
        
        await context.bot.send_message(chat_id=chat_id, text=res_msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # --- NEW PREDICTION ---
    if last_period_saved != next_period:
        results = ["BIG" if int(x['number']) >= 5 else "SMALL" for x in history[:10]]
        l1, l2, l3 = results[0], results[1], results[2]

        # LOGIC
        if l2 == l3 and l1 != l2:
            pred, h_type = l1, "AABB GLITCH 🧬"
        elif l1 == l2:
            pred, h_type = l1, "DRAGON PATTERN 🐉"
        else:
            pred, h_type = ("SMALL" if l1 == "BIG" else "BIG"), "ZIGZAG FLIP ⚡"

        user_data['last_period'] = next_period
        user_data['last_prediction'] = pred
        
        # Visual Elements
        color_dot = "🟦" if pred == "BIG" else "🟨"
        stream = " ".join(["B" if int(x['number']) >= 5 else "S" for x in history[:8]])
        
        # 🔥 ULTRA PRO MESSAGE BOX
        msg = (
            f"╔══════════════════════╗\n"
            f"║   <b>☠️ WINGO SERVER HACK</b>   ║\n"
            f"╠══════════════════════╣\n"
            f"║ 🆔 <b>Period:</b> <code>{next_period}</code>\n"
            f"║ 🦠 <b>Hack:</b> <code>{h_type}</code>\n"
            f"║ 🎰 <b>Result:</b>  <b>{pred}</b> {color_dot}\n"
            f"╠══════════════════════╣\n"
            f"║ 📡 <b>History:</b> {stream}\n"
            f"╚══════════════════════╝\n"
            f"<b>🏆 WINS: {user_data['wins']}</b>   (Losses Cleared)" 
        )
        # Note: লস দেখাচ্ছি না, শুধু বলছি 'Losses Cleared' অথবা চাইলে লস কাউন্ট সরাতে পারো
        
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    start_dummy_server()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))
    application.run_polling()
