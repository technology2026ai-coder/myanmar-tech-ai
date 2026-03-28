import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from groq import Groq

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# API Keys များကို Environment Variables မှယူမည်
TELEGRAM_TOKEN = os.getenv("8518235371:AAGSm--Yw-cZaOwWGGv6EC_LFV87C7ZMgq0")
GROQ_API_KEY = os.getenv("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")

client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! ကျွန်တော်က Groq AI နဲ့ ချိတ်ဆက်ထားတဲ့ Bot ပါ။ ဘာကူညီပေးရမလဲခင်ဗျာ?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    try:
        # Groq API သို့ ပေးပို့ခြင်း
        completion = client.chat.completions.create(
            model="llama3-8b-8192", # သင်ကြိုက်တဲ့ model ပြောင်းနိုင်ပါတယ်
            messages=[{"role": "user", "content": user_text}],
        )
        ai_response = completion.choices[0].message.content
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("တောင်းပန်ပါတယ်၊ အခုလောလောဆယ် Error တက်နေပါတယ်။")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("Error: API Tokens များ ထည့်သွင်းရန် လိုအပ်ပါသည်။")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running with Groq...")
    app.run_polling()
