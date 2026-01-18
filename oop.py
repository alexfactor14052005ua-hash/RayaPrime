import os
import logging
import sqlite3
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class RayaPrimeBot:
    def __init__(self, api_key, token):
        # Настройка Gemini ИИ
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.token = token
        # Имя базы из настроек Render
        self.db_name = os.getenv('DB_NAME', 'kuzmenko2')
        self.init_db()

    def init_db(self):
        """Создает таблицу для токенов, если её нет"""
        conn = sqlite3.connect(f"{self.db_name}.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id INTEGER PRIMARY KEY,
                token TEXT
            )
        ''')
        conn.commit()
        conn.close()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"🤖 Рая Прайм запущена!\n"
            f"База данных: {self.db_name}\n"
            f"Используйте /add_token <ваш_токен>, чтобы сохранить данные."
        )

    async def add_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Твоя функция добавления токенов в базу"""
        if not context.args:
            await update.message.reply_text("❌ Введите токен после команды. Пример: /add_token мой_секрет")
            return
        
        user_id = update.effective_user.id
        new_token = context.args[0]
        
        conn = sqlite3.connect(f"{self.db_name}.db")
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO user_tokens (user_id, token) VALUES (?, ?)', (user_id, new_token))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Токен успешно сохранен в базу {self.db_name}!")

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Ответ от ИИ Gemini
            response = self.model.generate_content(update.message.text)
            await update.message.reply_text(response.text)
        except Exception as e:
            logging.error(f"Ошибка ИИ: {e}")
            await update.message.reply_text("❌ Ошибка связи с нейросетью.")

    def run(self):
        app = Application.builder().token(self.token).build()
        
        # Регистрация команд
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("add_token", self.add_token))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        
        print(f"--- Протокол Райя Прайм запущен на базе {self.db_name} ---")
        app.run_polling()

if __name__ == '__main__':
    # Читаем переменные из Render Environment
    key = os.getenv('GROQ_API_KEY') 
    token = os.getenv('BOT_TOKEN')
    
    if key and token:
        RayaPrimeBot(key, token).run()
    else:
        print("❌ ОШИБКА: Ключи не найдены в Environment Variables!")
        print(f"GROQ_API_KEY: {'OK' if key else 'MISSING'}")
        print(f"BOT_TOKEN: {'OK' if token else 'MISSING'}")
