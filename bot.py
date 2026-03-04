import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

# إعدادات البوت
TOKEN = os.getenv("8660231924:AAHTh_vrZ8fVivPV-6Tv6M8apq3S--rdlOM")
ADMIN_ID = 8105131895   # الايدي بتاعك
CHANNEL_USERNAME = "@S70vNews"  # قناة الاشتراك الإجباري

logging.basicConfig(level=logging.INFO)

# قاعدة البيانات
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    target_id INTEGER,
    message TEXT
)
""")
conn.commit()

# تحقق الاشتراك
async def check_subscription(user_id, bot):
    member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
    return member.status in ["member", "administrator", "creator"]

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_subscription(user.id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ لازم تشترك في القناة الأول عشان تستخدم البوت.",
            reply_markup=reply_markup
        )
        return

    if context.args:
        target_id = int(context.args[0])
        context.user_data["target"] = target_id
        await update.message.reply_text("📝 ابعت رسالتك المجهولة الآن:")
    else:
        link = f"https://t.me/{context.bot.username}?start={user.id}"
        await update.message.reply_text(
            f"👋 أهلاً {user.first_name}\n\n"
            f"🔗 ده لينك الصراحة بتاعك:\n{link}\n\n"
            f"انشره واستقبل رسائل مجهولة 😏"
        )

# التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "target" in context.user_data:
        target_id = context.user_data["target"]
        sender = update.effective_user
        cursor.execute(
            "INSERT INTO messages (sender_id, target_id, message) VALUES (?, ?, ?)",
            (sender.id, target_id, update.message.text)
        )
        conn.commit()
        count = cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE target_id=?",
            (target_id,)
        ).fetchone()[0]
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📩 رسالة مجهولة جديدة:\n\n{update.message.text}\n\n📊 إجمالي الرسائل: {count}"
        )
        await update.message.reply_text("✅ تم إرسال رسالتك بنجاح!")
        context.user_data.clear()

# أمر الإحصائيات
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE target_id=?",
        (user_id,)
    ).fetchone()[0]
    await update.message.reply_text(f"📊 إجمالي الرسائل اللي وصلتك: {count}")

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
