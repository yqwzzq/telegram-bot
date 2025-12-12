import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6795286721

# Küfür listesi
def load_bad_words():
    try:
        with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except:
        return []

bad_words = load_bad_words()
user_stats = {}
bot_active = True

async def safe_delete(message):
    try:
        await message.delete()
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    await update.message.reply_text("Selam sahip")

async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = False
    await update.message.reply_text("by")

async def onpanic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = True
    await update.message.reply_text("hi")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    stats_lines = []
    for uid, info in user_stats.items():
        if uid == ADMIN_ID:
            continue
        nick_part = f"@{info['nick']} " if info['nick'] else ""
        join_str = info['join_date'].strftime("%Y-%m-%d %H:%M:%S")
        stats_lines.append(f"{nick_part}(ID: {uid} - {info['swear_count']} küfür) - Giriş: {join_str}")
    await update.message.reply_text("İstatistikler:\n" + ("\n".join(stats_lines) if stats_lines else "Henüz istatistik yok."))

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_stats
    if not bot_active:
        await safe_delete(update.message)
        return
    user = update.effective_user
    if user.id == ADMIN_ID:
        return
    text = update.message.text.lower()
    for word in bad_words:
        if word in text:
            await safe_delete(update.message)
            now = datetime.now()
            if user.id not in user_stats:
                user_stats[user.id] = {"swear_count": 1, "join_date": now, "nick": user.username}
            else:
                user_stats[user.id]["swear_count"] += 1
            return

# Yeni yapı: Application yerine Application(asyncio)
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panic", panic))
    app.add_handler(CommandHandler("onpanic", onpanic))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()  # eski Updater yerine bu çağrı kullanılacak
    await app.updater.idle()  # botu açık tutar

if __name__ == "__main__":
    asyncio.run(main())
