import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı! .env dosyasını veya Render Environment Variable'ı kontrol et.")

ADMIN_ID = 6795286721  # fake id

# Küfür listesi
def load_bad_words():
    try:
        with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except FileNotFoundError:
        print("kufur_listesi.txt bulunamadı!")
        return []

bad_words = load_bad_words()

user_stats = {}  # {user_id: {"swear_count": int, "join_date": datetime, "nick": str}}
bot_active = True

# Güvenli mesaj silme
async def safe_delete(message):
    try:
        await message.delete()
    except Exception:
        pass

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    await update.message.reply_text("Selam sahip")

# /panic
async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = False
    await update.message.reply_text("by")

# /onpanic
async def onpanic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = True
    await update.message.reply_text("hi")

# /stats
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

    if not stats_lines:
        await update.message.reply_text("Henüz istatistik yok.")
        return

    await update.message.reply_text("İstatistikler:\n" + "\n".join(stats_lines))

# Mesaj kontrolü
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

# Bot oluştur
app = ApplicationBuilder().token(TOKEN).build()

# Handler ekle
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panic", panic))
app.add_handler(CommandHandler("onpanic", onpanic))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))

# Botu çalıştır
if __name__ == "__main__":
    app.run_polling()
