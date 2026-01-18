import os
import json
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)

class RayaPrimeBot:
    def __init__(self, api_key, token):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.token = token
        self.db_name = os.getenv('DB_NAME', 'kuzmenko2')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🤖 Рая Прайм готова! База: {self.db_name}")

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = self.model.generate_content(update.message.text)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")

    def run(self):
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        print("--- Протокол Райя Прайм запущен ---")
        app.run_polling()

if __name__ == '__main__':
    key = os.getenv('GEMINI_API_KEY')
    token = os.getenv('BOT_TOKEN')
    if key and token:
        RayaPrimeBot(key, token).run()
    else:
        print("❌ Ключи не найдены в Environment!")
