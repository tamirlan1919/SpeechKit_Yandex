import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers import router
from database import create_all_tables
from database.repository import add_daily_requests  # Ваша функция для обновления request_month и пр.
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
from output.bot.handlers.noitification import handle_notification



# Функция для запуска aiohttp-сервера
async def on_startup(dispatcher: Dispatcher):
    app = web.Application()
    # Добавляем роут для уведомлений
    app.router.add_post('/send_notification', handle_notification)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()  # Запускаем сервер
    print("aiohttp сервер запущен на порту 3000")


async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    # Создаем все таблицы в базе данных
    await create_all_tables()
    print("Все таблицы успешно созданы")

    # Запускаем aiohttp сервер (запускается в отдельной задаче)
    asyncio.create_task(on_startup(dp))

    # Настраиваем планировщик (AsyncIOScheduler)
    scheduler = AsyncIOScheduler()
    # Добавляем задачу, которая будет запускаться каждый день в 02:00
    scheduler.add_job(add_daily_requests, trigger='cron', hour=2, minute=0)
    scheduler.start()
    print("Планировщик запущен")

    # Отправляем уведомление о старте бота (укажите свой chat_id)
    asyncio.create_task(bot.send_message(5455171373, 'Бот запущен'))

    # Запускаем polling бота
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    # Запуск основного цикла через asyncio.run, который создаст и установит event loop
    asyncio.run(main())
