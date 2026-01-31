# backend/bot/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database.database import init_db
from bot.handlers import start, reminders, settings_handlers
from bot.utils.scheduler import init_scheduler, scheduler

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# Подключение роутеров
dp.include_router(start.router)
dp.include_router(reminders.router)
dp.include_router(settings_handlers.router)

async def on_startup():
    """Действия при запуске"""
    logger.info("Инициализация базы данных...")
    await init_db()
    
    logger.info("Запуск планировщика...")
    await init_scheduler(bot)
    
    logger.info("Бот запущен!")

async def on_shutdown():
    """Действия при остановке"""
    logger.info("Остановка планировщика...")
    if scheduler:
        await scheduler.stop()
    
    logger.info("Бот остановлен")

async def main():
    """Запуск бота"""
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())