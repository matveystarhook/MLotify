# backend/database/repositories/user_repo.py

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from database.models import User, Category

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(
        self, 
        telegram_id: int, 
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "ru",
        timezone: str = "Europe/Moscow"
    ) -> User:
        """Создать нового пользователя с дефолтными категориями"""
        
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language=language,
            timezone=timezone
        )
        
        self.session.add(user)
        await self.session.flush()  # Получаем ID пользователя
        
        # Создаём дефолтные категории
        default_categories = [
            {"name": "Личное", "icon": "👤", "color": "#6C5CE7", "order": 1},
            {"name": "Работа", "icon": "💼", "color": "#0984E3", "order": 2},
            {"name": "Учёба", "icon": "📚", "color": "#00B894", "order": 3},
            {"name": "Здоровье", "icon": "💪", "color": "#E17055", "order": 4},
            {"name": "Покупки", "icon": "🛒", "color": "#FDCB6E", "order": 5},
        ]
        
        for cat_data in default_categories:
            category = Category(
                user_id=user.id,
                is_default=True,
                **cat_data
            )
            self.session.add(category)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> tuple[User, bool]:
        """Получить или создать пользователя. Возвращает (user, is_new)"""
        
        user = await self.get_by_telegram_id(telegram_id)
        
        if user:
            # Обновляем last_active и данные профиля
            user.last_active = datetime.utcnow()
            user.first_name = first_name
            user.username = username
            user.last_name = last_name
            await self.session.commit()
            return user, False
        
        # Создаём нового
        user = await self.create(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            last_name=last_name
        )
        return user, True
    
    async def update_settings(
        self,
        user_id: int,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        notifications_enabled: Optional[bool] = None,
        theme: Optional[str] = None
    ) -> User:
        """Обновить настройки пользователя"""
        
        update_data = {}
        if language is not None:
            update_data["language"] = language
        if timezone is not None:
            update_data["timezone"] = timezone
        if notifications_enabled is not None:
            update_data["notifications_enabled"] = notifications_enabled
        if theme is not None:
            update_data["theme"] = theme
        
        if update_data:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await self.session.execute(query)
            await self.session.commit()
        
        return await self.get_by_id(user_id)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по внутреннему ID"""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def increment_stats(
        self, 
        user_id: int, 
        created: int = 0, 
        completed: int = 0
    ):
        """Увеличить счётчики статистики"""
        user = await self.get_by_id(user_id)
        if user:
            user.total_reminders_created += created
            user.total_reminders_completed += completed
            await self.session.commit()