# backend/bot/utils/scheduler.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot

from database.database import async_session
from database.repositories.reminder_repo import ReminderRepository
from database.models import Reminder, ReminderStatus, RepeatType

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Планировщик напоминаний"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._check_interval = 30  # Проверка каждые 30 секунд
    
    async def start(self):
        """Запуск планировщика"""
        
        # Основная задача проверки напоминаний
        self.scheduler.add_job(
            self._check_pending_reminders,
            trigger=IntervalTrigger(seconds=self._check_interval),
            id="check_reminders",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Планировщик запущен")
    
    async def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")
    
    async def _check_pending_reminders(self):
        """Проверяет и отправляет уведомления"""
        
        try:
            now = datetime.utcnow()
            
            async with async_session() as session:
                repo = ReminderRepository(session)
                
                # Получаем напоминания, которые нужно отправить
                pending = await repo.get_pending_notifications(now)
                
                for reminder in pending:
                    await self._send_notification(reminder)
                    await repo.mark_notified(reminder.id)
                    
                    # Обрабатываем повторяющиеся
                    if reminder.repeat_type != RepeatType.NONE:
                        await self._schedule_next_occurrence(reminder, repo)
                
                if pending:
                    logger.info(f"Отправлено {len(pending)} уведомлений")
                    
        except Exception as e:
            logger.error(f"Ошибка проверки напоминаний: {e}")
    
    async def _send_notification(self, reminder: Reminder):
        """Отправляет уведомление пользователю"""
        
        try:
            # Формируем текст
            text = self._format_notification(reminder)
            
            # Клавиатура с действиями
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.button(
                text="✅ Выполнено",
                callback_data=f"complete_{reminder.id}"
            )
            builder.button(
                text="⏰ +15 мин",
                callback_data=f"snooze_{reminder.id}_15"
            )
            builder.button(
                text="⏰ +1 час",
                callback_data=f"snooze_{reminder.id}_60"
            )
            builder.adjust(1, 2)
            
            # Получаем telegram_id пользователя
            async with async_session() as session:
                from database.repositories.user_repo import UserRepository
                user_repo = UserRepository(session)
                user = await user_repo.get_by_id(reminder.user_id)
                
                if user:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=text,
                        reply_markup=builder.as_markup()
                    )
                    logger.info(f"Уведомление отправлено: {reminder.id} -> {user.telegram_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления {reminder.id}: {e}")
    
    def _format_notification(self, reminder: Reminder) -> str:
        """Форматирует текст уведомления"""
        
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡",
            "high": "🔴"
        }
        
        emoji = priority_emoji.get(reminder.priority.value, "🔔")
        
        text = f"""
{emoji} <b>Напоминание!</b>

📝 {reminder.title}
"""
        
        if reminder.description:
            text += f"\n📋 {reminder.description}"
        
        if reminder.category:
            text += f"\n\n{reminder.category.icon} {reminder.category.name}"
        
        return text.strip()
    
    async def _schedule_next_occurrence(
        self, 
        reminder: Reminder, 
        repo: ReminderRepository
    ):
        """Создаёт следующее повторение напоминания"""
        
        next_time = self._calculate_next_occurrence(reminder)
        
        if next_time:
            # Проверяем, не превышена ли дата окончания
            if reminder.repeat_end_date and next_time > reminder.repeat_end_date:
                return
            
            # Создаём новое напоминание
            await repo.create(
                user_id=reminder.user_id,
                title=reminder.title,
                description=reminder.description,
                remind_at=next_time,
                category_id=reminder.category_id,
                priority=reminder.priority,
                repeat_type=reminder.repeat_type,
                repeat_days=reminder.repeat_days,
                repeat_end_date=reminder.repeat_end_date
            )
    
    def _calculate_next_occurrence(self, reminder: Reminder) -> Optional[datetime]:
        """Вычисляет время следующего повторения"""
        
        current = reminder.remind_at
        
        if reminder.repeat_type == RepeatType.DAILY:
            return current + timedelta(days=1)
        
        elif reminder.repeat_type == RepeatType.WEEKLY:
            return current + timedelta(weeks=1)
        
        elif reminder.repeat_type == RepeatType.MONTHLY:
            # Следующий месяц, та же дата
            month = current.month + 1
            year = current.year
            if month > 12:
                month = 1
                year += 1
            
            try:
                return current.replace(year=year, month=month)
            except ValueError:
                # Если дня нет в месяце (31 февраля), берём последний день
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                return current.replace(year=year, month=month, day=last_day)
        
        elif reminder.repeat_type == RepeatType.WEEKDAYS:
            # Пропускаем выходные
            next_day = current + timedelta(days=1)
            while next_day.weekday() >= 5:  # 5=суббота, 6=воскресенье
                next_day += timedelta(days=1)
            return next_day
        
        elif reminder.repeat_type == RepeatType.CUSTOM:
            # Выбранные дни недели
            if not reminder.repeat_days:
                return None
            
            allowed_days = [int(d) - 1 for d in reminder.repeat_days.split(",")]
            next_day = current + timedelta(days=1)
            
            for _ in range(7):
                if next_day.weekday() in allowed_days:
                    return next_day
                next_day += timedelta(days=1)
        
        return None


# Глобальный экземпляр
scheduler: Optional[ReminderScheduler] = None

def get_scheduler() -> ReminderScheduler:
    global scheduler
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return scheduler

async def init_scheduler(bot: Bot):
    global scheduler
    scheduler = ReminderScheduler(bot)
    await scheduler.start()