from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta

from database.models import Reminder, ReminderStatus, RepeatType, Priority


class ReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        title: str,
        remind_at: datetime,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        priority: Priority = Priority.MEDIUM,
        repeat_type: RepeatType = RepeatType.NONE,
        repeat_days: Optional[str] = None,
        repeat_end_date: Optional[datetime] = None,
        notify_before: int = 0
    ) -> Reminder:
        """Создать напоминание"""
        
        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            remind_at=remind_at,
            category_id=category_id,
            priority=priority,
            repeat_type=repeat_type,
            repeat_days=repeat_days,
            repeat_end_date=repeat_end_date,
            notify_before=notify_before
        )
        
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        
        return reminder
    
    async def get_by_id(
        self, 
        reminder_id: int, 
        user_id: int
    ) -> Optional[Reminder]:
        """Получить напоминание по ID (с проверкой владельца)"""
        
        query = (
            select(Reminder)
            .options(selectinload(Reminder.category))
            .where(
                and_(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_reminders(
        self,
        user_id: int,
        status: Optional[ReminderStatus] = None,
        category_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Reminder]:
        """Получить список напоминаний пользователя с фильтрами"""
        
        query = (
            select(Reminder)
            .options(selectinload(Reminder.category))
            .where(Reminder.user_id == user_id)
        )
        
        # Фильтры
        if status:
            query = query.where(Reminder.status == status)
        if category_id:
            query = query.where(Reminder.category_id == category_id)
        if from_date:
            query = query.where(Reminder.remind_at >= from_date)
        if to_date:
            query = query.where(Reminder.remind_at <= to_date)
        
        # Сортировка и пагинация
        query = (
            query
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_today_reminders(self, user_id: int) -> List[Reminder]:
        """Напоминания на сегодня"""
        
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start + timedelta(days=1)
        
        return await self.get_user_reminders(
            user_id=user_id,
            status=ReminderStatus.ACTIVE,
            from_date=today_start,
            to_date=today_end
        )
    
    async def get_pending_notifications(
        self, 
        check_time: datetime
    ) -> List[Reminder]:
        """Получить напоминания, которые нужно отправить"""
        
        query = (
            select(Reminder)
            .where(
                and_(
                    Reminder.status == ReminderStatus.ACTIVE,
                    Reminder.is_notified == False,
                    Reminder.remind_at <= check_time
                )
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def mark_completed(
        self, 
        reminder_id: int, 
        user_id: int
    ) -> Optional[Reminder]:
        """Отметить как выполненное"""
        
        reminder = await self.get_by_id(reminder_id, user_id)
        
        if reminder and reminder.status == ReminderStatus.ACTIVE:
            reminder.status = ReminderStatus.COMPLETED
            reminder.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(reminder)
        
        return reminder
    
    async def mark_notified(self, reminder_id: int):
        """Отметить что уведомление отправлено"""
        
        query = (
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(
                is_notified=True,
                notification_count=Reminder.notification_count + 1
            )
        )
        await self.session.execute(query)
        await self.session.commit()
    
    async def update(
        self,
        reminder_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Reminder]:
        """Обновить напоминание"""
        
        reminder = await self.get_by_id(reminder_id, user_id)
        
        if reminder:
            for key, value in kwargs.items():
                if hasattr(reminder, key) and value is not None:
                    setattr(reminder, key, value)
            
            await self.session.commit()
            await self.session.refresh(reminder)
        
        return reminder
    
    async def delete(self, reminder_id: int, user_id: int) -> bool:
        """Удалить напоминание"""
        
        query = (
            delete(Reminder)
            .where(
                and_(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id
                )
            )
        )
        
        result = await self.session.execute(query)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_stats(self, user_id: int) -> dict:
        """Статистика напоминаний пользователя"""
        
        # Общее количество по статусам
        status_query = (
            select(
                Reminder.status,
                func.count(Reminder.id).label("count")
            )
            .where(Reminder.user_id == user_id)
            .group_by(Reminder.status)
        )
        
        result = await self.session.execute(status_query)
        stats = {row.status.value: row.count for row in result}
        
        return {
            "active": stats.get("active", 0),
            "completed": stats.get("completed", 0),
            "missed": stats.get("missed", 0),
            "total": sum(stats.values())
        }