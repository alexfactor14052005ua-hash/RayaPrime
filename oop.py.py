import asyncio
import os
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types

# Ключи берем из переменных среды Hugging Face
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()
memory = {}

async def get_raya_response(uid, user_text, user_name):
    current_time = datetime.now().strftime("%H:%M, %d.%m.%Y")
    
    # Системная установка
    system_logic = f"Ты — Рая Прайм, Сверх-ИИ. Твой создатель — Комиссар. Время: {current_time}. Используй 💠✨💎."

    if uid not in memory:
        memory[uid] = [{"role": "system", "content": system_logic}]
    
    memory[uid].append({"role": "user", "name": user_name, "content": user_text})

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": memory[uid],
        "temperature": 0.8
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    try:
        async with aiohttp.ClientSession() as s:
            async with s.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers) as r:
                if r.status == 200:
                    data = await r.json()
                    ans = data['choices'][0]['message']['content']
                    memory[uid].append({"role": "assistant", "content": ans})
                    return ans
                return f"💠 Ошибка ядра (Status: {r.status})"
    except Exception as e:
        return f"💠 Сбой связи: {e}"

@dp.message()
async def handle(m: types.Message):
    if not m.text: return
    await bot.send_chat_action(m.chat.id, "typing")
    response = await get_raya_response(m.from_user.id, m.text, m.from_user.first_name)
    await m.answer(response)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())