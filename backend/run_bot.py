import asyncio
import logging
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import uvicorn

from config import settings
from database.database import init_db
from bot.handlers import start, reminders, settings_handlers
from bot.utils.scheduler import init_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(reminders.router)
dp.include_router(settings_handlers.router)

def run_api():
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")

async def main():
    await init_db()
    logger.info("✅ Database initialized")
    
    await init_scheduler(bot)
    logger.info("✅ Scheduler started")
    
    # API в отдельном потоке
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("✅ API started on http://localhost:8000")
    
    logger.info("✅ Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())