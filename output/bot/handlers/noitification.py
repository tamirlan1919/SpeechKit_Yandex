from aiogram.enums import ParseMode
from aiohttp import web
from aiogram import Bot


from output.bot.config import TOKEN, voice_descriptions, roleLabels
from output.bot.database.db import AsyncSessionLocal
from output.bot.database.repository import get_count_symbol_all

bot = Bot(TOKEN)  # Убедитесь, что импортирован ваш токен

async def handle_notification(request):
    data = await request.json()
    user_id = data.get("user_id")
    selected_voice = data.get("selected_voice")
    selected_speed = data.get("selected_speed")
    role = data.get("role")

    await send_notification(user_id, selected_voice, selected_speed, role)
    return web.Response(text="Notification sent")


async def send_notification(user_id: int, selected_voice: str, selected_speed: float, role: str):
    async with AsyncSessionLocal() as db:
        selected_voice = voice_descriptions[selected_voice]
        count = await get_count_symbol_all(db) or 700
        if role == 'undefined':
            role = 'Нейтральный'
        else:
            role = roleLabels[role]
        message = (
            f"Ваши настройки сохранены:\n"
            f"Спикер: {selected_voice}\n"
            f"Скорость: {selected_speed}\n"
            f"Роль: {role}"
            f'\n\nОтправьте текст для озвучки (до {count} символов).'
        )
        await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
