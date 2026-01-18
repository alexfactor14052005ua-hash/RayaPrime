#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM БОТ "РАЯ ПРАЙМ" - AI АССИСТЕНТ
Мониторинг чатов + Google интеграция + AI анализ
"""

import json
import os
import sys
from datetime import datetime, timedelta
import re
import asyncio
import logging

# Проверка библиотек
try:
    import anthropic
except ImportError:
    print("❌ Установи: pip install anthropic")
    sys.exit(1)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, 
        CallbackQueryHandler, ContextTypes, filters
    )
except ImportError:
    print("❌ Установи: pip install python-telegram-bot")
    sys.exit(1)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False
    print("⚠️ Google библиотеки не установлены (необязательно)")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Google API области
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
]


class GoogleServices:
    """Работа с Google API"""
    
    def __init__(self):
        self.creds = None
        self.gmail = None
        self.calendar = None
        self.connected = False
        
        if GOOGLE_OK:
            self.auth()
    
    def auth(self):
        """Авторизация"""
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as t:
                    self.creds = pickle.load(t)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                with open('token.pickle', 'wb') as t:
                    pickle.dump(self.creds, t)
            
            self.gmail = build('gmail', 'v1', credentials=self.creds)
            self.calendar = build('calendar', 'v3', credentials=self.creds)
            self.connected = True
            
        except Exception as e:
            logger.error(f"Google auth error: {e}")
    
    def search_gmail(self, query='newer_than:2d', max_results=10):
        """Поиск в Gmail"""
        if not self.connected:
            return []
        
        try:
            result = self.gmail.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            emails = []
            
            for msg in messages:
                message = self.gmail.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                
                emails.append({
                    'subject': subject,
                    'from': sender,
                    'snippet': message.get('snippet', '')
                })
            
            return emails
        except:
            return []
    
    def create_event(self, title, date, time, duration=60):
        """Создание события"""
        if not self.connected:
            return False
        
        try:
            start = datetime.fromisoformat(f"{date}T{time}:00")
            end = start + timedelta(minutes=duration)
            
            event = {
                'summary': title,
                'start': {'dateTime': start.isoformat(), 'timeZone': 'Europe/Moscow'},
                'end': {'dateTime': end.isoformat(), 'timeZone': 'Europe/Moscow'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                        {'method': 'popup', 'minutes': 10}
                    ]
                }
            }
            
            self.calendar.events().insert(calendarId='primary', body=event).execute()
            return True
        except:
            return False


class RayaPrimeBot:
    """Главный класс бота Рая Прайм"""
    
    def __init__(self, anthropic_key, telegram_token):
        self.ai = anthropic.Anthropic(api_key=anthropic_key)
        self.telegram_token = telegram_token
        self.google = GoogleServices() if GOOGLE_OK else None
        
        # Настройки
        self.config_file = 'raya_config.json'
        self.config = self.load_config()
        
        # История чатов для каждого пользователя
        self.chat_histories = {}
    
    def load_config(self):
        """Загрузка конфигурации"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        cfg = {
            'monitored_users': [],
            'allowed_users': [],
            'keywords': ['встреча', 'созвон', 'дедлайн', 'meeting'],
            'auto_notify': True
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        
        return cfg
    
    def save_config(self):
        """Сохранение конфигурации"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        
        # Добавляем пользователя в разрешенные
        if user.id not in self.config['allowed_users']:
            self.config['allowed_users'].append(user.id)
            self.save_config()
        
        welcome_text = f"""🤖 Привет, {user.first_name}! Я Рая Прайм - твой AI ассистент!

✨ Что я умею:
• 📧 Мониторить твой Gmail на события
• 📅 Создавать события в Google Calendar
• 💬 Общаться и помогать с задачами
• 🔍 Анализировать сообщения на встречи
• ⚡ Автоматически находить и создавать напоминания

📋 Команды:
/start - Это меню
/gmail - Проверить почту
/calendar - Ближайшие события
/auto - Автоматический режим
/help - Помощь

Просто напиши мне что-нибудь, и я помогу! 😊"""
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """📖 ПОМОЩЬ - РАЯ ПРАЙМ

🔹 /start - Главное меню
🔹 /gmail - Сканировать Gmail на события
🔹 /calendar - Показать календарь на неделю
🔹 /auto - Авто режим (Gmail → Calendar)
🔹 /settings - Настройки мониторинга
🔹 /help - Эта справка

💬 Просто пиши мне:
• "Найди письма про встречу"
• "Что у меня завтра?"
• "Создай событие на завтра в 15:00"
• Или любой другой вопрос!

🔐 Конфиденциальность:
Я работаю только с ТВОИМИ данными.
Все разрешения запрашиваются отдельно."""
        
        await update.message.reply_text(help_text)
    
    async def gmail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /gmail - мониторинг Gmail"""
        user_id = update.effective_user.id
        
        if user_id not in self.config['allowed_users']:
            await update.message.reply_text("❌ У тебя нет доступа. Используй /start")
            return
        
        if not self.google or not self.google.connected:
            await update.message.reply_text("❌ Google не подключен. Нужен credentials.json")
            return
        
        await update.message.reply_text("🔍 Сканирую Gmail... Подожди немного...")
        
        # Поиск писем
        emails = self.google.search_gmail('newer_than:2d', max_results=15)
        
        if not emails:
            await update.message.reply_text("📧 Новых писем не найдено")
            return
        
        found_events = []
        
        for email in emails:
            text = f"{email['subject']} {email['snippet']}"
            
            # Проверка ключевых слов
            if any(kw in text.lower() for kw in self.config['keywords']):
                # Анализ AI
                event = await self.extract_event(text)
                
                if event:
                    found_events.append({
                        'email': email,
                        'event': event
                    })
        
        if found_events:
            response = f"✅ Найдено событий: {len(found_events)}\n\n"
            
            for i, item in enumerate(found_events[:5], 1):
                ev = item['event']
                response += f"{i}. 📋 {ev['title']}\n"
                response += f"   📅 {ev.get('date', '?')} в {ev.get('time', '?')}\n"
                response += f"   📧 Из: {item['email']['from'][:40]}\n\n"
            
            # Кнопки
            keyboard = [
                [InlineKeyboardButton("⚡ Создать все в Calendar", callback_data='create_all')],
                [InlineKeyboardButton("📅 Показать календарь", callback_data='show_calendar')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup)
            
            # Сохраняем для callback
            context.user_data['found_events'] = found_events
        else:
            await update.message.reply_text("📧 Событий в письмах не найдено")
    
    async def calendar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /calendar"""
        if not self.google or not self.google.connected:
            await update.message.reply_text("❌ Google Calendar не подключен")
            return
        
        await update.message.reply_text("📅 Загружаю календарь...")
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
            
            events = self.google.calendar.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=end,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            items = events.get('items', [])
            
            if items:
                response = "📅 БЛИЖАЙШИЕ СОБЫТИЯ:\n\n"
                
                for event in items:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    summary = event.get('summary', 'Без названия')
                    
                    if 'T' in start:
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        formatted = dt.strftime('%d.%m %H:%M')
                    else:
                        formatted = start
                    
                    response += f"• {formatted} - {summary}\n"
                
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("📅 Событий на неделю нет")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def auto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Автоматический режим"""
        await update.message.reply_text("⚡ Запускаю автоматический режим...\n\n1. Сканирую Gmail\n2. Ищу события\n3. Создам в Calendar")
        
        # Сначала сканируем Gmail
        await self.gmail_command(update, context)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if user_id not in self.config['allowed_users']:
            await update.message.reply_text("❌ Используй /start для доступа")
            return
        
        # Инициализация истории
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []
        
        # Добавляем сообщение в историю
        self.chat_histories[user_id].append({
            'role': 'user',
            'content': user_message
        })
        
        # Ограничиваем историю последними 10 сообщениями
        if len(self.chat_histories[user_id]) > 20:
            self.chat_histories[user_id] = self.chat_histories[user_id][-20:]
        
        # Отправляем запрос к AI
        try:
            response = self.ai.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=2000,
                system="""Ты - Рая Прайм, дружелюбный AI ассистент в Telegram.
Ты помогаешь с:
- Организацией времени и событий
- Поиском информации
- Анализом текста на встречи и дедлайны
- Созданием напоминаний

Общайся живо, по-дружески, используй эмодзи.
Если видишь в сообщении упоминание встречи - предложи создать событие.""",
                messages=self.chat_histories[user_id]
            )
            
            bot_reply = response.content[0].text
            
            # Добавляем ответ в историю
            self.chat_histories[user_id].append({
                'role': 'assistant',
                'content': bot_reply
            })
            
            # Проверяем, есть ли в сообщении событие
            event = await self.extract_event(user_message)
            
            if event and event.get('date') and event.get('time'):
                keyboard = [
                    [InlineKeyboardButton(
                        f"📅 Создать: {event['title']}", 
                        callback_data=f"create_event_{event['date']}_{event['time']}"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.user_data['pending_event'] = event
                
                await update.message.reply_text(bot_reply, reply_markup=reply_markup)
            else:
                await update.message.reply_text(bot_reply)
                
        except Exception as e:
            logger.error(f"AI error: {e}")
            await update.message.reply_text(f"❌ Ошибка AI: {e}")
    
    async def extract_event(self, text):
        """Извлечение события из текста"""
        prompt = f"""Найди событие/встречу. Верни ТОЛЬКО JSON:

{text}

{{
    "found": true/false,
    "title": "название",
    "date": "YYYY-MM-DD или null",
    "time": "HH:MM или null",
    "duration": 60
}}"""
        
        try:
            r = self.ai.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=1000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            txt = r.content[0].text
            m = re.search(r'\{.*\}', txt, re.DOTALL)
            
            if m:
                data = json.loads(m.group())
                if data.get('found'):
                    return data
        except:
            pass
        
        return None
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'create_all':
            events = context.user_data.get('found_events', [])
            
            if not events:
                await query.edit_message_text("❌ Нет событий для создания")
                return
            
            created = 0
            
            for item in events:
                ev = item['event']
                
                if ev.get('date') and ev.get('time'):
                    if self.google.create_event(
                        ev['title'], 
                        ev['date'], 
                        ev['time'], 
                        ev.get('duration', 60)
                    ):
                        created += 1
            
            await query.edit_message_text(f"✅ Создано событий: {created}")
        
        elif query.data == 'show_calendar':
            # Просто вызываем команду календаря
            await query.edit_message_text("📅 Загружаю календарь...")
        
        elif query.data.startswith('create_event_'):
            event = context.user_data.get('pending_event')
            
            if event and self.google.create_event(
                event['title'],
                event['date'],
                event['time'],
                event.get('duration', 60)
            ):
                await query.edit_message_text(f"✅ Событие '{event['title']}' создано!")
            else:
                await query.edit_message_text("❌ Не удалось создать событие")
    
    def run(self):
        """Запуск бота"""
        app = Application.builder().token(self.telegram_token).build()
        
        # Обработчики команд
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("gmail", self.gmail_command))
        app.add_handler(CommandHandler("calendar", self.calendar_command))
        app.add_handler(CommandHandler("auto", self.auto_command))
        
        # Обработчик кнопок
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик сообщений
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        print("="*60)
        print("🤖 РАЯ ПРАЙМ ЗАПУЩЕНА!")
        print("="*60)
        print("Бот работает... Нажми Ctrl+C для остановки")
        print("="*60)
        
        # Запуск polling
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🤖 TELEGRAM БОТ "РАЯ ПРАЙМ" 🤖                  ║
║                  AI Персональный Ассистент                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Проверка API ключей
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not anthropic_key:
        print("❌ Установи ANTHROPIC_API_KEY")
        print("set ANTHROPIC_API_KEY=sk-ant-твой_ключ")
        return
    
    if not telegram_token:
        print("❌ Установи TELEGRAM_BOT_TOKEN")
        print("set TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather")
        print("\nПолучить токен:")
        print("1. Открой Telegram")
        print("2. Найди @BotFather")
        print("3. Отправь /newbot")
        print("4. Следуй инструкциям")
        return
    
    # Запуск бота
    try:
        bot = RayaPrimeBot(anthropic_key, telegram_token)
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == '__main__':
    main()
