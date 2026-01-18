import json
import os
import sys
from datetime import datetime, timedelta
import re
import logging
import google.generativeai as genai # Вместо anthropic

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, 
        CallbackQueryHandler, ContextTypes, filters
    )
except ImportError:
    sys.exit(1)

# Твой блок Google API (без изменений)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False

class RayaPrimeBot:
    def __init__(self, gemini_key, telegram_token):
        # Настройка под твой ключ Gemini
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.telegram_token = telegram_token
        self.db_name = os.getenv('DB_NAME', 'kuzmenko2')
        self.chat_histories = {}

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🤖 Рая Прайм запущена!\nБаза: {self.db_name}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_message = update.message.text
        try:
            # Общение через Gemini (как в оригинале, но без ошибок)
            chat = self.chat_histories.get(user_id, self.model.start_chat(history=[]))
            response = chat.send_message(f"Ты Рая Прайм. Ответь: {user_message}")
            self.chat_histories[user_id] = chat
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")

    def run(self):
        app = Application.builder().token(self.telegram_token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        app.run_polling()

if __name__ == '__main__':
    # Берем те имена, что ты вписал на Render
    api_key = os.getenv('GEMINI_API_KEY')
    token = os.getenv('BOT_TOKEN')
    if api_key and token:
        RayaPrimeBot(api_key, token).run()
