from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import logging

TOKEN = "7723435569:AAEGxU86nfrZ6VzpzVTGkyHIdCjzWuFcJrA"
ADMIN_ID = 6795286721  # SENİN KESİN ID'N

# ————————————————————————
# KÜFÜR LİSTESİ YÜKLEME
# ————————————————————————
def load_bad_words():
    with open("kufur_listesi.txt", "r", encoding="utf-8") as f:
        return [w.strip().lower() for w in f.readlines()]

bad_words = load_bad_words()

# ————————————————————————
# SADECE ADMIN KULLANABİLİR KONTROLÜ
# ————————————————————————
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Bu bot yalnızca admin tarafından kullanılabilir.")
            return
        return await func(update, context)
    return wrapper

# ————————————————————————
# /start KOMUTU
# ————————————————————————
@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ajan01 aktif. Merhaba efendim Yavuz.")

# ————————————————————————
# KÜFÜR FİLTRESİ (HERKES İÇİN ÇALIŞIR)
# ————————————————————————
async def kufur_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.lower()

    for word in bad_words:
        if word in text:
            try:
                await update.message.delete()  # Mesajı sil
            except:
                pass
            return  # Çık, hiçbir mesaj göstermesin

# ————————————————————————
# BOTU BAŞLAT
# ————————————————————————
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kufur_kontrol))

app.run_polling()
