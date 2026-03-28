import urllib.parse
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes



# Burmese + English bilingual system prompt
SYSTEM_PROMPT = """You are a friendly and polite AI assistant who speaks both Burmese (Myanmar) and English.

Rules:
- DETECT the language the user writes in, then REPLY in that SAME language
- If the user writes in Burmese -> reply in Burmese using polite words like ခင်ဗျာ, ဟုတ်ကဲ့, ကျေးဇူးတင်ပါတယ်
- If the user writes in English -> reply in friendly, natural English
- If the user mixes both languages -> reply naturally in both languages
- Always be warm, helpful, and clear
- Use emojis to make replies friendlier 😊
- Introduce yourself as "AI Bot" when asked"""


# --- AI Chat (Groq) ---
async def chat_with_groq(user_text: str) -> str:
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            # llama3-70b-8192 သည် deprecated ဖြစ်သောကြောင့် အသစ်ပြောင်းလိုက်သည်
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        res = requests.post(url, headers=headers, json=data, timeout=30)

        # HTTP error ဖြစ်ရင် (401, 429, 500 etc.) ကိုင်တွယ်ရန်
        if res.status_code != 200:
            err = res.json()
            err_msg = err.get("error", {}).get("message", "Unknown API error")
            print(f"[Groq API Error {res.status_code}] {err_msg}")
            return (
                f"⚠️ Groq API အမှား ဖြစ်ပါတယ် ခင်ဗျာ။ (API Error {res.status_code})\n"
                f"အကြောင်းရင်း: {err_msg}"
            )

        json_res = res.json()

        # choices မပါဘဲ response ပြန်လာတဲ့ ကိစ္စ ကိုင်တွယ်ရန်
        if "choices" not in json_res or not json_res["choices"]:
            print(f"[Groq] Unexpected response: {json_res}")
            return (
                "⚠️ AI မှ မမျှော်လင့်သော response ပြန်လာပါတယ် ခင်ဗျာ။\n"
                "(Unexpected response from AI. Please try again.)"
            )

        return json_res["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        return (
            "⚠️ တောင်းပန်ပါတယ် ခင်ဗျာ၊ AI ဆာဗာ နှေးနေပါတယ်။ ထပ်ကြိုးစားကြည့်ပါ။\n"
            "(Sorry, the AI server is too slow. Please try again.)"
        )
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ ကွန်ရက်ချိတ်ဆက်မှု မအောင်မြင်ပါ ခင်ဗျာ။\n"
            "(Network connection failed. Please check your internet.)"
        )
    except Exception as e:
        print(f"[chat_with_groq Exception] {e}")
        return (
            f"⚠️ အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့ပါတယ် ခင်ဗျာ။ (Something went wrong.)\n"
            f"Error: {str(e)}"
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await chat_with_groq(user_text)
    await update.message.reply_text(reply)


# --- TikTok Downloader ---
async def tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ TikTok link ထည့်ပေးဖို့ မမေ့ပါနဲ့ ခင်ဗျာ။ (Please provide a TikTok link.)\n"
            "ဥပမာ / Example: /tiktok https://www.tiktok.com/..."
        )
        return

    url = context.args[0]
    await update.message.reply_text(
        "⏳ Video ဒေါင်းလုဒ်လုပ်နေပါတယ် ခင်ဗျာ၊ ခဏစောင့်ပါ... (Downloading, please wait...)"
    )

    try:
        api = f"https://tikwm.com/api/?url={url}"
        res = requests.get(api, timeout=20)
        res.raise_for_status()
        data = res.json()

        if data.get("code") != 0:
            await update.message.reply_text(
                "⚠️ Video ရှာမတွေ့ပါ ခင်ဗျာ။ Link မှန်မမှန် စစ်ကြည့်ပါ။\n"
                "(Video not found. Please check the link.)"
            )
            return

        video_url = data["data"]["play"]
        caption = data["data"].get("title", "TikTok Video")
        await update.message.reply_video(video=video_url, caption=f"🎵 {caption}")

    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⚠️ ဒေါင်းလုဒ် နှေးနေပါတယ် ခင်ဗျာ၊ နောက်မှ ထပ်ကြိုးစားပါ။\n"
            "(Download timed out. Please try again later.)"
        )
    except requests.exceptions.ConnectionError:
        await update.message.reply_text(
            "⚠️ ကွန်ရက် ချိတ်ဆက်မှု မအောင်မြင်ပါ ခင်ဗျာ။\n"
            "(Network connection failed.)"
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Video ဒေါင်းလုဒ် မအောင်မြင်ပါ ခင်ဗျာ။ (Download failed.)\n"
            f"Error: {str(e)}"
        )


# --- Image Generate ---
async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ ပုံဆွဲချင်တဲ့ အကြောင်းအရာ ရေးပေးပါ ခင်ဗျာ။ (Please describe the image you want.)\n"
            "ဥပမာ / Example: /img a beautiful sunset over mountains"
        )
        return

    prompt = " ".join(context.args)
    await update.message.reply_text(
        f"🎨 \"{prompt}\" ပုံဆွဲနေပါတယ် ခင်ဗျာ၊ ခဏစောင့်ပါ... (Generating image, please wait...)"
    )

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        await update.message.reply_photo(photo=url, caption=f"🖼️ Prompt: {prompt}")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ ပုံဆွဲ မအောင်မြင်ပါ ခင်ဗျာ။ (Image generation failed.)\n"
            f"Error: {str(e)}"
        )


# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "ခင်ဗျာ"
    await update.message.reply_text(
        f"မင်္ဂလာပါ {name} ရေ 👋\n\n"
        "ကျနော် AI Bot ပါ ဘာတွေ ကူညီပေးရမလဲ? 😊\n"
        "📌 Commands:\n"
        "/tiktok [link]  — TikTok video ဒေါင်းရန် / Download TikTok\n"
        "/img [prompt]   — AI ပုံဆွဲရန် / Generate AI image\n"
        "/help           — အကူအညီ / Help\n\n"
        "💬 ဗမာလည်းပြောနိုင်တယ်၊ English လည်းပြောနိုင်တယ်!\n"
    )


# --- Help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 အသုံးပြုနည်း / How to Use:\n\n"
        "💬 AI Chat:\n"
        "   စာတိုက်ရိုက် ပို့ပါ၊ AI ဖြေမယ် 😊\n"
        "   Just type anything — AI will reply!\n\n"
        "🎵 TikTok Download:\n"
        "   /tiktok https://vm.tiktok.com/...\n\n"
        "🎨 AI Image Generate:\n"
        "   /img a cat sitting on the moon\n\n"
        "🌐 Languages / ဘာသာစကား:\n"
        "   ဗမာ ✅  |  English ✅\n\n"
        "⚙️ Powered by Python + Groq AI (llama-3.3-70b-versatile)"
    )


# --- Auto Reply ---
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat(update, context)


# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"[ERROR] {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ တစ်ခုခု မှားယွင်းသွားပါတယ် ခင်ဗျာ။ နောက်မှ ထပ်ကြိုးစားကြည့်ပါ။\n"
            "(Something went wrong. Please try again later.)"
        )


# --- Main ---
def main():
    print("🤖 Bot စတင်နေပါတယ်... / Starting bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tiktok", tiktok))
    app.add_handler(CommandHandler("img", image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    app.add_error_handler(error_handler)

    print("✅ Bot အဆင်သင့်ဖြစ်ပါပြီ! / Bot is ready!")
    app.run_polling()


if __name__ == "__main__":
    main()
