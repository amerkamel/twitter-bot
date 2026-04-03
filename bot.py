import re
import os
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ============================================================
# ✏️ ضع معلوماتك هنا فقط
# ============================================================

# 1️⃣ التوكن يُسحب تلقائياً من Railway Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8716320633:AAEoxpkixadtga3XvsaBhdlatbIaa8cB7CQ")

# 2️⃣ آيدي الأدمن — غيّر هذا الرقم لآيديك
ADMIN_ID = 235030882

# 3️⃣ قنوات الاشتراك الإجباري
CHANNELS = [
    {
        "id":   "@ccmmt",
        "name": "عنب ",
        "link": "https://t.me/ccmmt"
    },
    # أضف قناة ثانية هنا إذا تريد:
    # {"id": "@قناة2", "name": "قناة 2", "link": "https://t.me/قناة2"},
]

# 4️⃣ API التنزيل — اتركه fxtwitter، وإذا توقف غيّره لـ vxtwitter
ACTIVE_API = "fxtwitter"

# ============================================================
# 🔧 لا تغير شيئاً تحت هذا السطر
# ============================================================

API_URLS = {
    "fxtwitter": "https://api.fxtwitter.com/status/{}",
    "vxtwitter": "https://api.vxtwitter.com/status/{}",
}

users_db = set()
download_count = {"total": 0}

async def get_unsubscribed(user_id, context):
    missing = []
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch["id"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                missing.append(ch)
        except:
            missing.append(ch)
    return missing

def build_sub_keyboard(missing):
    buttons = [[InlineKeyboardButton(f"📢 اشترك ← {ch['name']}", url=ch["link"])] for ch in missing]
    buttons.append([InlineKeyboardButton("✅ اشتركت، تحقق الآن", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["📥 تنزيل فيديو/صورة"], ["📊 إحصائيات", "❓ مساعدة"]],
        resize_keyboard=True
    )

def fetch_media(tweet_url):
    if "t.co" in tweet_url:
        try:
            r = requests.head(tweet_url, allow_redirects=True, timeout=8)
            tweet_url = r.url
        except:
            pass
    match = re.search(r"(?:twitter\.com|x\.com)/\w+/status/(\d+)", tweet_url)
    if not match:
        return None
    tweet_id = match.group(1)
    api_url = API_URLS.get(ACTIVE_API, API_URLS["fxtwitter"]).format(tweet_id)
    try:
        r = requests.get(api_url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        data = r.json()
        tweet = data.get("tweet", {})
        media = tweet.get("media", {})
        videos, images, gifs = [], [], []
        for v in media.get("videos", []):
            variants = sorted(
                [x for x in v.get("variants", []) if x.get("content_type") == "video/mp4"],
                key=lambda x: x.get("bitrate", 0), reverse=True
            )
            if variants:
                videos.append({"high": variants[0]["url"], "low": variants[-1]["url"]})
        for g in media.get("gifs", []):
            variants = g.get("variants", [])
            if variants:
                gifs.append(variants[0]["url"])
        for p in media.get("photos", []):
            url = p.get("url", "")
            if url:
                images.append(url + ("" if "?" in url else "?format=jpg&name=orig"))
        return {"videos": videos, "images": images, "gifs": gifs, "text": tweet.get("text", "")}
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_db.add(user.id)
    missing = await get_unsubscribed(user.id, context)
    if missing:
        await update.message.reply_text(
            f"👋 أهلاً {user.first_name}!\n\n⚠️ اشترك في القنوات أولاً:",
            reply_markup=build_sub_keyboard(missing)
        )
        return
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"👤 مستخدم جديد!\nالاسم: {user.full_name}\nاليوزر: @{user.username or 'لا يوجد'}\nالآيدي: {user.id}\nإجمالي: {len(users_db)}"
        )
    except:
        pass
    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}! 🎉\n\n"
        "🐦 أرسل رابط أي تغريدة من تويتر/X\n"
        "وسأنزّل لك الفيديو والصور مباشرة ✅\n\n"
        "يدعم: فيديو 🎬 | صور 🖼️ | GIF 🎞️",
        reply_markup=main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ *طريقة الاستخدام:*\n\n"
        "1️⃣ انسخ رابط أي تغريدة من تويتر/X\n"
        "2️⃣ أرسله هنا مباشرة\n"
        "3️⃣ انتظر ثوانٍ وستصلك الملفات ✅\n\n"
        "*الروابط المدعومة:*\n"
        "• twitter.com/user/status/...\n"
        "• x.com/user/status/...\n"
        "• روابط t.co المختصرة\n\n"
        "*المحتوى المدعوم:*\n"
        "🎬 فيديو بجودة عالية\n"
        "🖼️ صور بأعلى جودة\n"
        "🎞️ GIF",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 *إحصائيات البوت:*\n\n"
        f"👥 عدد المستخدمين: {len(users_db)}\n"
        f"📥 إجمالي التنزيلات: {download_count['total']}\n"
        f"🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode="Markdown"
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not context.args:
        await update.message.reply_text("📢 الاستخدام: /broadcast الرسالة هنا")
        return
    msg_text = " ".join(context.args)
    success, failed = 0, 0
    status_msg = await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(users_db)} مستخدم...")
    for uid in users_db:
        try:
            await context.bot.send_message(uid, f"📢 *رسالة من الإدارة:*\n\n{msg_text}", parse_mode="Markdown")
            success += 1
        except:
            failed += 1
    await status_msg.edit_text(f"✅ تم!\nنجح: {success}\nفشل: {failed}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not context.args:
        await update.message.reply_text("🚫 الاستخدام: /ban آيدي_المستخدم")
        return
    try:
        ban_id = int(context.args[0])
        users_db.discard(ban_id)
        await update.message.reply_text(f"✅ تم حظر {ban_id}")
    except:
        await update.message.reply_text("❌ آيدي غير صحيح")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    users_db.add(user.id)
    if text == "❓ مساعدة":
        await help_command(update, context)
        return
    if text == "📊 إحصائيات":
        await stats_command(update, context)
        return
    if text == "📥 تنزيل فيديو/صورة":
        await update.message.reply_text("أرسل رابط التغريدة 👇", reply_markup=main_keyboard())
        return
    missing = await get_unsubscribed(user.id, context)
    if missing:
        await update.message.reply_text("⚠️ اشترك في القنوات أولاً!", reply_markup=build_sub_keyboard(missing))
        return
    if "twitter.com" not in text and "x.com" not in text and "t.co" not in text:
        await update.message.reply_text("❌ أرسل رابط تغريدة من تويتر أو X فقط.", reply_markup=main_keyboard())
        return
    msg = await update.message.reply_text("⏳ جاري جلب المحتوى...")
    media = fetch_media(text)
    if not media or (not media["videos"] and not media["images"] and not media["gifs"]):
        await msg.edit_text("❌ لا يوجد فيديو أو صور في هذه التغريدة.")
        return
    total = len(media["videos"]) + len(media["images"]) + len(media["gifs"])
    await msg.edit_text(f"⬇️ جاري إرسال {total} ملف...")
    for i, video in enumerate(media["videos"]):
        try:
            await update.message.reply_video(video=video["high"], caption=f"🎬 فيديو {i+1} ✅", supports_streaming=True)
            download_count["total"] += 1
        except:
            try:
                await update.message.reply_video(video=video["low"], caption=f"🎬 فيديو {i+1} ✅", supports_streaming=True)
                download_count["total"] += 1
            except:
                await update.message.reply_text(f"⚠️ تعذّر إرسال فيديو {i+1}")
    for i, gif_url in enumerate(media["gifs"]):
        try:
            await update.message.reply_animation(animation=gif_url, caption=f"🎞️ GIF {i+1} ✅")
            download_count["total"] += 1
        except:
            pass
    for i, img_url in enumerate(media["images"]):
        try:
            await update.message.reply_photo(photo=img_url, caption=f"🖼️ صورة {i+1}/{len(media['images'])} ✅")
            download_count["total"] += 1
        except:
            pass
    await msg.delete()

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    missing = await get_unsubscribed(query.from_user.id, context)
    if missing:
        await query.edit_message_text("❌ لم تشترك بعد!", reply_markup=build_sub_keyboard(missing))
    else:
        await query.edit_message_text("✅ ممتاز! أرسل الآن رابط أي تغريدة 🎉")
        await context.bot.send_message(query.from_user.id, "🐦 أرسل رابط التغريدة!", reply_markup=main_keyboard())

if __name__ == "__main__":
    print("🤖 البوت يعمل...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
