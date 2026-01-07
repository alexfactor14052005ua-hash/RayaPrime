import os
import logging
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Переменные для Render
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
client = genai.Client(api_key=GEMINI_KEY)

RAYA_PROMPT = "Ты — Райя Прайм, продвинутый ИИ. Твой тон вежливый и технологичный."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=update.message.text,
            config=types.GenerateContentConfig(system_instruction=RAYA_PROMPT)
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("⚠ Модуль Райя: Ошибка связи.")

if __name__ == '__main__':
    if TOKEN and GEMINI_KEY:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        print("--- Протокол Райя Прайм запущен ---")
        app.run_polling()
