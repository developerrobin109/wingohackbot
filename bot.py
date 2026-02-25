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
BOT_TOKEN = "8451758265:AAE59kkZqp7R7A-riOyDVlpZ5_Ljj6Vfc3E"
ACCESS_PASSWORD = "robin1235"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# 🔥 ফ্রি প্রক্সি লিস্ট (অটোমেটিক রোটেট করবে)
PROXIES = [
    "http://202.162.212.164:80",
    "http://103.152.112.162:80",
    "http://124.70.16.24:8080",
    "http://47.251.50.117:80",
    "http://20.210.113.32:80",
    "http://103.49.202.252:80"
]
# ----------------------------------------------- #

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER (Render-এ বট যাতে না ঘুমায়) ---
class SimpleHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Running')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTP)
    server.serve_forever()

def start_dummy_server():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
# -----------------------------------------------

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
        "<b>🔒 TERMINAL LOCKED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛑 <b>SESSION EXPIRED</b>\n"
        "👤 <b>USER:</b> <code>Guest</code>\n"
        "🛡️ <b>SECURITY:</b> <code>AES-256</code>\n"
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
        
        # হ্যাকার স্টাইল এনিমেশন
        msg = await update.message.reply_text("🔄 <b>Connecting to Satellite...</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.5)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="🔓 <b>Credentials Verified!</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.5)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"{BANNER}\n✅ <b>ACCESS GRANTED</b>\n🚀 <b>PROXY PROTECTION ACTIVE</b>", parse_mode=ParseMode.HTML)
        
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id, name=str(chat_id))
    else:
        await update.message.reply_html("❌ <b>ACCESS DENIED!</b>")

def fetch_data():
    """Anti-Ban Data Fetcher (Proxy Rotation)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.ar-lottery01.com/'
    }
    params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}

    # ১. প্রথমে ডাইরেক্ট চেষ্টা
    try:
        res = requests.get(API_URL, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            return res.json()['data']['list']
    except:
        pass 

    # ২. ডাইরেক্ট ফেইল হলে প্রক্সি দিয়ে চেষ্টা
    for _ in range(3):
        try:
            proxy = random.choice(PROXIES)
            res = requests.get(API_URL, headers=headers, params=params, proxies={"http": proxy, "https": proxy}, timeout=5)
            if res.status_code == 200:
                return res.json()['data']['list']
        except:
            continue
    
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

    # WIN/LOSS
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            res_msg = f"✅ <b>WIN!</b> <code>{real_res}</code> 💰"
        else:
            user_data['losses'] += 1
            res_msg = f"❌ <b>LOSS!</b> <code>{real_res}</code> 💀"
        
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
        
        color_dot = "🔵" if pred == "BIG" else "🟡"
        stream = " ".join(["B" if int(x['number']) >= 5 else "S" for x in history[:8]])
        
        msg = (
            f"╔════════════════════╗\n"
            f"║ 💀 <b>WINGO VIP HACK</b> 💀\n"
            f"╠════════════════════╣\n"
            f"║ 🎯 <b>Target:</b> <code>{next_period}</code>\n"
            f"║ 🦠 <b>Type:</b> <code>{h_type}</code>\n"
            f"║ 🔮 <b>Predict:</b> <b>{pred}</b> {color_dot}\n"
            f"╠════════════════════╣\n"
            f"║ 📡 <b>Stream:</b> {stream}\n"
            f"╚════════════════════╝\n"
            f"🏆 Wins: {user_data['wins']}  |  💀 Loss: {user_data['losses']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    start_dummy_server()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))
    application.run_polling()