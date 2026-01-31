# backend/database/repositories/category_repo.py

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from database.models import Category

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, 
        category_id: int, 
        user_id: int
    ) -> Optional[Category]:
        """Получить категорию по ID"""
        
        query = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_categories(self, user_id: int) -> List[Category]:
        """Получить все категории пользователя"""
        
        query = (
            select(Category)
            .where(Category.user_id == user_id)
            .order_by(Category.order, Category.id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self,
        user_id: int,
        name: str,
        icon: str = "📌",
        color: str = "#6C5CE7"
    ) -> Category:
        """Создать категорию"""
        
        # Определяем порядок (последняя + 1)
        max_order_query = (
            select(func.max(Category.order))
            .where(Category.user_id == user_id)
        )
        result = await self.session.execute(max_order_query)
        max_order = result.scalar() or 0
        
        category = Category(
            user_id=user_id,
            name=name,
            icon=icon,
            color=color,
            order=max_order + 1,
            is_default=False
        )
        
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        
        return category
    
    async def update(
        self,
        category_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Category]:
        """Обновить категорию"""
        
        category = await self.get_by_id(category_id, user_id)
        
        if category:
            for key, value in kwargs.items():
                if hasattr(category, key) and value is not None:
                    setattr(category, key, value)
            
            await self.session.commit()
            await self.session.refresh(category)
        
        return category
    
    async def delete(self, category_id: int, user_id: int) -> bool:
        """Удалить категорию (только если не дефолтная)"""
        
        category = await self.get_by_id(category_id, user_id)
        
        if category and not category.is_default:
            await self.session.delete(category)
            await self.session.commit()
            return True
        
        return False
    
    async def reorder(
        self, 
        user_id: int, 
        category_ids: List[int]
    ) -> List[Category]:
        """Изменить порядок категорий"""
        
        for order, cat_id in enumerate(category_ids):
            await self.session.execute(
                update(Category)
                .where(
                    Category.id == cat_id,
                    Category.user_id == user_id
                )
                .values(order=order)
            )
        
        await self.session.commit()
        return await self.get_user_categories(user_id)