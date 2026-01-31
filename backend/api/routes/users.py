# backend/api/routes/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_session
from database.repositories.user_repo import UserRepository
from database.repositories.reminder_repo import ReminderRepository
from api.auth import get_current_user, TelegramUser
from api.schemas import (
    UserResponse, UserUpdateRequest, 
    StatsResponse, SuccessResponse
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить информацию о текущем пользователе"""
    
    repo = UserRepository(session)
    
    user, is_new = await repo.get_or_create(
        telegram_id=telegram_user.id,
        first_name=telegram_user.first_name,
        username=telegram_user.username,
        last_name=telegram_user.last_name
    )
    
    return user

@router.patch("/me", response_model=UserResponse)
async def update_user_settings(
    data: UserUpdateRequest,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Обновить настройки пользователя"""
    
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await repo.update_settings(
        user_id=user.id,
        **data.model_dump(exclude_none=True)
    )
    
    return updated_user

@router.get("/me/stats", response_model=StatsResponse)
async def get_user_stats(
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить статистику пользователя"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reminder_repo = ReminderRepository(session)
    stats = await reminder_repo.get_stats(user.id)
    
    # Вычисляем процент выполнения
    total = stats["completed"] + stats["missed"]
    completion_rate = (stats["completed"] / total * 100) if total > 0 else 0
    
    return StatsResponse(
        active=stats["active"],
        completed=stats["completed"],
        missed=stats["missed"],
        total=stats["total"],
        completion_rate=round(completion_rate, 1),
        current_streak=user.current_streak,
        best_streak=user.best_streak
    )