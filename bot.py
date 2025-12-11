import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler

# SADECE SENİN ID — tek admin sensin
ADMIN_IDS = {851176709}

# TOKENİN EKLENDİ
TOKEN = "7723435569:AAEcGZIJjIU2UmhSVt6ds5EyM74Fv-5iKXQ"

# KÜFÜR LİSTESİYİ OKUYAN FONKSİYON
def load_bad_words():
    if os.path.exists("kufur_listesi.txt"):
        with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f.readlines()]
    return []

BAD_WORDS = load_bad_words()

# /start KOMUTU
async def start(update, context):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu bot yalnızca admin tarafından kullanılabilir.")
        return
    
    await update.message.reply_text("👑 Bot aktif aşkım. Her şey kontrolüm altında 💛")

# KÜFÜR FİLTRESİ
async def filter_bad_words(update, context):
    user_id = update.effective_user.id
    if not update.message:
        return

    text = update.message.text.lower()

    # Küfür içeriyor mu bak
    if any(bad in text for bad in BAD_WORDS):
        # Mesajı sil
        try:
            await update.message.delete()
        except:
            pass

        # Adminse sadece uyar
        if user_id in ADMIN_IDS:
            await update.message.reply_text("⚠️ Küfür tespit edildi ama sen admin olduğun için silmedim.")
        else:
            await update.message.reply_text("❌ Küfür yasak.")

# UYGULAMA
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad_words))

if __name__ == "__main__":
    print("Bot çalışıyor...")
    app.run_polling()

