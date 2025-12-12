import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# .env dosyasından tokeni çek
TOKEN = os.getenv("BOT_TOKEN")

# Sadece admin ID
ADMIN_ID = 6795286721  # fake id

# Küfür listesi dosyadan yükleniyor
def load_bad_words():
    with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f.readlines()]

bad_words = load_bad_words()

# Kullanıcı istatistikleri
user_stats = {}  # {user_id: {"swear_count": int, "join_date": datetime, "nick": str}}

# Botun durumu (panic/onpanic)
bot_active = True

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.delete()
        return
    await update.message.reply_text("Selam sahip")

# /panic komutu
async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.delete()
        return
    bot_active = False
    await update.message.reply_text("by")

# /onpanic komutu
async def onpanic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.delete()
        return
    bot_active = True
    await update.message.reply_text("hi")

# /stats komutu
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.delete()
        return

    stats_lines = []
    for uid, info in user_stats.items():
        if uid == ADMIN_ID:
            continue  # admin istatistiklerde görünmeyecek
        nick_part = f"@{info['nick']} " if info['nick'] else ""
        # join_date'i her zaman güncel formatla
        join_str = info['join_date'].strftime("%Y-%m-%d %H:%M:%S")
        stats_lines.append(f"{nick_part}(ID: {uid} - {info['swear_count']} küfür) - Giriş: {join_str}")

    if not stats_lines:
        await update.message.reply_text("Henüz istatistik yok.")
        return

    stats_text = "\n".join(stats_lines)
    await update.message.reply_text(f"İstatistikler:\n{stats_text}")

# Mesaj kontrolü
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_stats
    if not bot_active:
        await update.message.delete()
        return

    user = update.effective_user
    user_id = user.id
    username = user.username
    text = update.message.text.lower()

    # Admin küfürlerini sayma
    if user_id == ADMIN_ID:
        return

    # Küfür kontrolü
    for word in bad_words:
        if word in text:
            await update.message.delete()
            # Kullanıcı kaydı oluştur veya güncelle
            now = datetime.now()
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "swear_count": 1,
                    "join_date": now,
                    "nick": username
                }
            else:
                user_stats[user_id]["swear_count"] += 1
                # Her mesajda join_date'i sabit bırakıyoruz, sadece güncel saat istatistiği gösterilebilir
            return

# Uygulama oluştur
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
