import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ENV variables
BOT_TOKEN = os.getenv("8750432897:AAH3R9ILWNaBbDGMBpcCCZIbCzlNUdi8OAA")
GROQ_API_KEY = os.getenv("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")

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hello! I'm your AI bot.\n"
        "I can reply in English + Myanmar 😊\n"
        "Message me anything!"
    )

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a polite and friendly assistant. "
                        "Always reply in a mix of English and Myanmar language. "
                        "Use simple words. Be gentle, respectful, and helpful. "
                        "Explain step-by-step like a teacher. "
                        "Add some friendly emojis in replies."
                    )
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"❌ Error: {e}"

    await update.message.reply_text(reply)

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
