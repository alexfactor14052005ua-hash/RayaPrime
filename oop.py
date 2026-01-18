import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логи, чтобы видеть сообщения в панели Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class RayaPrimeBot:
    def __init__(self, api_key, token):
        # Используем Gemini через твой ключ GROQ_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.token = token
        self.db_name = os.getenv('DB_NAME', 'kuzmenko2')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🤖 Рая Прайм запущена и готова! База: {self.db_name}")

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Отправляем сообщение пользователя в ИИ
            response = self.model.generate_content(update.message.text)
            await update.message.reply_text(response.text)
        except Exception as e:
            logging.error(f"Ошибка ИИ: {e}")
            await update.message.reply_text("💎 Рая: Ой, что-то пошло не так с нейросетью...")

    def run(self):
        # Создаем приложение бота
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        
        print(f"--- Протокол Райя Прайм запущен на базе {self.db_name} ---")
        app.run_polling()

if __name__ == '__main__':
    # ВНИМАНИЕ: Берем именно те имена, которые у тебя на скриншоте Render!
    key = os.getenv('GROQ_API_KEY') 
    token = os.getenv('BOT_TOKEN')
    
    if key and token:
        RayaPrimeBot(key, token).run()
    else:
        print("❌ ОШИБКА: Проверь ключи BOT_TOKEN и GROQ_API_KEY в настройках Render!")
