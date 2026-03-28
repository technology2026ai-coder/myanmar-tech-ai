import os
import urllib.parse
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are a friendly and polite AI assistant who speaks both Burmese (Myanmar) and English.
Rules:
- DETECT the language the user writes in, then REPLY in that SAME language
- If the user writes in Burmese -> reply in Burmese using polite words like ခင်ဗျာ, ဟုတ်ကဲ့, ကျေးဇူးတင်ပါတယ်
- If the user writes in English -> reply in friendly, natural English
- Always be warm, helpful, and clear
- Use emojis 😊"""


async def chat_with_groq(user_text: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=data, timeout=30
        )
        if res.status_code != 200:
            err = res.json().get("error", {}).get("message", "Unknown error")
            return f"⚠️ API Error {res.status_code}: {err}"
        json_res = res.json()
        if "choices" not in json_res or not json_res["choices"]:
            return "⚠️ AI မှ response မရပါ ခင်ဗျာ။ ထပ်ကြိုးစားပါ။"
        return json_res["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠️ AI ဆာဗာ နှေးနေပါတယ် ခင်ဗျာ။ ထပ်ကြိုးစားပါ။"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await chat_with_groq(update.message.text)
    await update.message.reply_text(reply)


async def tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ /tiktok https://www.tiktok.com/..."
        )
        return
    await update.message.reply_text("⏳ Downloading...")
    try:
        res = requests.get(
            f"https://tikwm.com/api/?url={context.args[0]}", timeout=20
        ).json()
        if res.get("code") != 0:
            await update.message.reply_text("⚠️ Video မတွေ့ပါ ခင်ဗျာ။")
            return
        await update.message.reply_video(
            video=res["data"]["play"],
            caption=f"🎵 {res['data'].get('title', '')}"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ /img a beautiful sunset")
        return
    prompt = " ".join(context.args)
    await update.message.reply_text(f"🎨 Generating: {prompt}")
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true"
        await update.message.reply_photo(photo=url, caption=f"🖼️ {prompt}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "ခင်ဗျာ"
    await update.message.reply_text(
        f"မင်္ဂလာပါ {name} ရေ 👋 | Hello {name}! 👋\n\n"
        "📌 Commands:\n"
        "/tiktok [link] — TikTok download\n"
        "/img [prompt] — AI image\n"
        "/help — Help\n\n"
        "💬 ဗမာ / English နှစ်မျိုးလုံး ပြောနိုင်တယ်!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 How to Use:\n\n"
        "💬 Chat: စာရိုက်လိုက်ရုံပဲ!\n"
        "🎵 /tiktok https://vm.tiktok.com/...\n"
        "🎨 /img a cat on the moon\n\n"
        "🌐 ဗမာ ✅ | English ✅"
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"[ERROR] {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ တစ်ခုခု မှားသွားပါတယ် ခင်ဗျာ။ ထပ်ကြိုးစားပါ။"
        )


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN မရှိပါ!")
        return
    print("🤖 Bot starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tiktok", tiktok))
    app.add_handler(CommandHandler("img", image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_error_handler(error_handler)
    print("✅ Bot is ready!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
