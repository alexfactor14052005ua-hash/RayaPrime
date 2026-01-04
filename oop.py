import os
import logging
import asyncio
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Читаем ключи из настроек Render
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)

# Инициализация Gemini
client = genai.Client(api_key=GEMINI_KEY)

RAYA_PROMPT = (
    "Ты — Райя Прайм, продвинутый ИИ-модуль из вселенной Лололошки. "
    "Твой тон: вежливый, высокотехнологичный. Ты используешь поиск Google для ответов."
)

# Инструмент поиска
search_tool = types.Tool(
    google_search_retrieval=types.GoogleSearchRetrieval(
        dynamic_retrieval_config=types.DynamicRetrievalConfig(
            mode=types.DynamicRetrievalConfigMode.MODE_DYNAMIC,
            dynamic_threshold=0.3
        )
    )
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Запрос к ИИ
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=RAYA_PROMPT,
                tools=[search_tool]
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("⚠ Райя: Обнаружена ошибка модуля связи.")

if __name__ == '__main__':
    if not TOKEN or not GEMINI_KEY:
        print("ОШИБКА: Ключи не найдены в Environment Variables!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        print("--- Протокол Райя Прайм запущен ---")
        app.run_polling()
