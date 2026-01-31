import asyncio
import logging
import os
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import uvicorn

from config import settings
from database.database import init_db
from bot.handlers import start, reminders, settings_handlers
from bot.utils.scheduler import init_scheduler

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Бот
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(reminders.router)
dp.include_router(settings_handlers.router)

def run_api():
    """Запуск API"""
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

async def main():
    # Инициализация БД
    await init_db()
    logger.info("✅ Database initialized")
    
    # Запуск планировщика
    await init_scheduler(bot)
    logger.info("✅ Scheduler started")
    
    # Запуск API в отдельном потоке
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("✅ API started")
    
    # Запуск бота
    logger.info("✅ Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())