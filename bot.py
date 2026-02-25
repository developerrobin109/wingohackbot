import logging
import requests
import asyncio
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER (Render Fix) ---
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
    
    # পুরোনো জব রিমুভ করা
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_html(
        f"{BANNER}\n<b>🔒 SYSTEM LOCKED</b>\n🔑 ENTER PASSWORD:"
    )

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
        context.user_data['fail_count'] = 0 # কানেকশন ফেইল কাউন্টার
        
        await update.message.reply_html("✅ <b>ACCESS GRANTED!</b>\n🚀 <b>CONNECTING TO SERVER...</b>")
        
        # লুপ চালু
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id, name=str(chat_id))
    else:
        await update.message.reply_text("❌ Wrong Password!")

def fetch_data():
    try:
        # লেটেস্ট হেডার্স (ব্লক এড়াতে)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.ar-lottery01.com/',
            'Origin': 'https://www.ar-lottery01.com'
        }
        params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}
        
        res = requests.get(API_URL, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()['data']['list']
        return None
    except Exception as e:
        return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_data = context.application.user_data[job.user_id]
    
    if not user_data.get('logged_in'):
        job.schedule_removal()
        return

    history = fetch_data()
    
    # --- কানেকশন এরর হ্যান্ডলিং ---
    if not history:
        user_data['fail_count'] = user_data.get('fail_count', 0) + 1
        
        # যদি ৫ বার চেষ্টা করেও কানেক্ট না হয়, তবে ইউজারকে জানাবে
        if user_data['fail_count'] == 5:
            await context.bot.send_message(
                chat_id=chat_id, 
                text="⚠️ <b>SERVER ERROR:</b> Render IP Blocked.\nTrying to reconnect...", 
                parse_mode=ParseMode.HTML
            )
            user_data['fail_count'] = 0 # রিসেট
        return
    # -----------------------------

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # RESULT CHECK
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            res_msg = f"✅ <b>WIN!</b> {real_res}"
        else:
            user_data['losses'] += 1
            res_msg = f"❌ <b>LOSS!</b> {real_res}"
        
        await context.bot.send_message(chat_id=chat_id, text=res_msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # PREDICTION
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
