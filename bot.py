import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# --- Ortam Değişkenlerini Güvenli Oku ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı! Ortam değişkenlerini kontrol edin.")

try:
    # ADMIN_ID'yi ortam değişkeninden oku ve tam sayıya çevir
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
except (TypeError, ValueError):
    raise ValueError("ADMIN_ID ortam değişkeni bulunamadı veya geçerli bir tam sayı değil!")

# --- Sabitler ve Dosya Yönetimi ---
STATS_FILE = "user_stats.json"

def get_file_path(filename):
    """Dağıtım ortamları için güvenli dosya yolunu döndürür."""
    # Bot dosyasının bulunduğu dizini alır
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

# Küfür listesini yükle (Güvenli dosya yolu kullanılarak)
def load_bad_words():
    """kufur_listesi.txt dosyasından kelimeleri yükler."""
    file_path = get_file_path("kufur_listesi.txt")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Tüm kelimeleri küçük harfe çevirip boşlukları temizler
            return {line.strip().lower() for line in f.readlines() if line.strip()}
    except FileNotFoundError:
        print(f"HATA: kufur_listesi.txt '{file_path}' yolunda bulunamadı!")
        return set() # Set kullanmak, arama performansını artırır

bad_words = load_bad_words()

# İstatistikleri Kaydetme/Yükleme Fonksiyonları
def save_stats(stats_data):
    """İstatistikleri JSON dosyasına kaydet."""
    serializable_stats = {}
    for uid, data in stats_data.items():
        # JSON anahtarları string olmalıdır
        serializable_stats[str(uid)] = {
            "swear_count": data["swear_count"],
            "join_date": data["join_date"].isoformat(), # datetime nesnesini string'e çevir
            "nick": data["nick"]
        }
    try:
        with open(get_file_path(STATS_FILE), "w", encoding="utf-8") as f:
            json.dump(serializable_stats, f, indent=4)
    except Exception as e:
        print(f"İstatistik kaydetme hatası: {e}")

def load_stats():
    """İstatistikleri JSON dosyasından yükle."""
    file_path = get_file_path(STATS_FILE)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_stats = json.load(f)
            deserialized_stats = {}
            for uid, data in loaded_stats.items():
                deserialized_stats[int(uid)] = { # Anahtarları int'e çevir
                    "swear_count": data["swear_count"],
                    "join_date": datetime.fromisoformat(data["join_date"]),
                    "nick": data["nick"]
                }
            return deserialized_stats
    except Exception as e:
        print(f"İstatistik dosyası yüklenirken hata oluştu: {e}")
        return {}

# Global değişkenler
user_stats = load_stats() # Bot başladığında istatistikleri yükle
bot_active = True

# Güvenli mesaj silme
async def safe_delete(message):
    """Hata durumunda sessizce mesajı silmeye çalışır."""
    try:
        await message.delete()
    except Exception:
        pass

# --- Handler Fonksiyonları ---

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Komut admin tarafından gönderilmediyse sil
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    await update.message.reply_text("Selam sahip. Küfür filtresi aktif.")

# /panic - Botu pasif moda alır
async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = False
    await update.message.reply_text("Bot pasif moda alındı (panic). Küfür kontrolü durduruldu.")

# /onpanic - Botu aktif moda alır
async def onpanic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return
    bot_active = True
    await update.message.reply_text("Bot aktif moda alındı.")

# /stats - İstatistikleri gösterir
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await safe_delete(update.message)
        return

    stats_lines = []
    # Küfür sayısına göre ters sırada sırala
    sorted_stats = sorted(user_stats.items(), key=lambda item: item[1]['swear_count'], reverse=True)
    
    for uid, info in sorted_stats:
        if uid == ADMIN_ID:
            continue
        # Kullanıcı adı yoksa ID ile göster
        nick_part = f"@{info['nick']} " if info['nick'] and info['nick'] != f"id_{uid}" else ""
        join_str = info['join_date'].strftime("%Y-%m-%d %H:%M")
        stats_lines.append(f"{nick_part}(ID: {uid}) - Küfür: {info['swear_count']} - Giriş: {join_str}")

    if not stats_lines:
        await update.message.reply_text("Henüz istatistik yok.")
        return

    await update.message.reply_text("İstatistikler (Küfür Sayısına Göre Sıralı):\n" + "\n".join(stats_lines))

# Mesaj kontrolü (Ana işlev)
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_stats
    
    user = update.effective_user
    
    # Bot pasif ise ve admin değilse mesajı sil
    if not bot_active and user.id != ADMIN_ID:
        await safe_delete(update.message)
        return

    if user.id == ADMIN_ID:
        return # Admin mesajlarını kontrol etme
    
    # Sadece metin mesajlarını işle
    if not update.message.text:
        return

    text = update.message.text.lower()
    
    # Küfür kontrolü
    for word in bad_words:
        # Küfür kelimesi metin içinde geçiyorsa
        if word in text:
            await safe_delete(update.message)
            
            # İstatistikleri güncelle
            now = datetime.now()
            user_id_str = user.id
            
            if user_id_str not in user_stats:
                user_stats[user_id_str] = {
                    "swear_count": 1, 
                    "join_date": now, 
                    "nick": user.username or f"id_{user_id_str}"
                }
            else:
                user_stats[user_id_str]["swear_count"] += 1
                
            save_stats(user_stats) # İstatistikleri diske kaydet
            return

# --- Ana Çalıştırma Bloğu ---

# Bot oluştur
app = ApplicationBuilder().token(TOKEN).build()

# Handler ekle
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panic", panic))
app.add_handler(CommandHandler("onpanic", onpanic))
app.add_handler(CommandHandler("stats", stats))
# Komut olmayan metin mesajlarını dinle
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))

# Botu çalıştır (Render ve diğer sunucu ortamları için önerilen yöntem)
if __name__ == "__main__":
    print("Bot çalışıyor. Çıkış için Ctrl+C.")
    # run_polling() yerine sunucu ortamları için daha uygun olan run_until_disconnected() kullanıldı
    app.run_until_disconnected()
