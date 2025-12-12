import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# .env dosyasından tokeni çek
TOKEN = os.getenv("BOT_TOKEN")

# Sadece admin ID
ADMIN_ID = 6795286721  # burayı kendi ID'inle değiştir

# Küfür listesi dosyadan yükleniyor
def load_bad_words():
    with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f.readlines()]

bad_words = load_bad_words()

# Kullanıcı istatistikleri (küfür sayısı)
user_stats = {}

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu bot yalnızca admin tarafından kullanılabilir.")
        return
    await update.message.reply_text("Ajan01 aktif. Merhaba admin!")

# Mesaj kontrolü
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.lower()

    # Küfür kontrolü
    for word in bad_words:
        if word in text:
            await update.message.delete()
            if user_id != ADMIN_ID:
                user_stats[user_id] = user_stats.get(user_id, 0) + 1
            return

# /stats komutu
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bu bot yalnızca admin tarafından kullanılabilir.")
        return

    if not user_stats:
        await update.message.reply_text("Henüz istatistik yok.")
    else:
        stats_text = "\n".join([f"{uid}: {count} küfür" for uid, count in user_stats.items()])
        await update.message.reply_text(f"📝 Kullanıcı istatistikleri:\n{stats_text}")

# Uygulama oluştur
app = ApplicationBuilder().token(TOKEN).build()

# Handler ekle
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))

# Botu çalıştır
if __name__ == "__main__":
    app.run_polling()
