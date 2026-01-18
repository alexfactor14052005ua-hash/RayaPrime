import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class RayaPrimeBot:
    def __init__(self, api_key, token):
        # Настройка Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.token = token
        self.db_name = os.getenv('DB_NAME', 'kuzmenko2')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🤖 Рая Прайм запущена!\nБаза данных: {self.db_name}")

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = self.model.generate_content(update.message.text)
            await update.message.reply_text(response.text)
        except Exception as e:
            logger.error(f"Ошибка ИИ: {e}")
            await update.message.reply_text("❌ Ошибка связи с нейросетью")

    def run(self):
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        
        print(f"--- БОТ РАБОТАЕТ НА БАЗЕ {self.db_name} ---")
        app.run_polling()

if __name__ == '__main__':
    # Читаем переменные именно так, как они называются у тебя на Render
    key = os.getenv('GROQ_API_KEY') 
    token = os.getenv('BOT_TOKEN')
    
    if key and token:
        try:
            RayaPrimeBot(key, token).run()
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    else:
        # Это та самая ошибка, которую ты видишь в логах
        print("❌ ОШИБКА: Ключи не найдены! Проверь названия в Environment.")
