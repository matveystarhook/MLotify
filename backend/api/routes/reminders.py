# backend/api/routes/reminders.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from database.database import get_session
from database.repositories.user_repo import UserRepository
from database.repositories.reminder_repo import ReminderRepository
from database.models import ReminderStatus
from api.auth import get_current_user, TelegramUser
from api.schemas import (
    ReminderCreate, ReminderUpdate, ReminderResponse,
    ReminderListResponse, ParseRequest, ParseResponse,
    SuccessResponse
)
from bot.utils.parser import parse_reminder_text

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.get("", response_model=ReminderListResponse)
async def get_reminders(
    status: Optional[str] = Query(None, description="active, completed, missed"),
    category_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить список напоминаний с фильтрами"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Преобразуем статус
    status_enum = None
    if status:
        try:
            status_enum = ReminderStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    repo = ReminderRepository(session)
    reminders = await repo.get_user_reminders(
        user_id=user.id,
        status=status_enum,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit + 1,  # +1 чтобы проверить has_more
        offset=offset
    )
    
    has_more = len(reminders) > limit
    if has_more:
        reminders = reminders[:limit]
    
    # Получаем общее количество
    stats = await repo.get_stats(user.id)
    total = stats["total"]
    
    return ReminderListResponse(
        items=reminders,
        total=total,
        has_more=has_more
    )

@router.get("/today", response_model=ReminderListResponse)
async def get_today_reminders(
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить напоминания на сегодня"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    reminders = await repo.get_today_reminders(user.id)
    
    return ReminderListResponse(
        items=reminders,
        total=len(reminders),
        has_more=False
    )

@router.post("", response_model=ReminderResponse)
async def create_reminder(
    data: ReminderCreate,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Создать напоминание"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    reminder = await repo.create(
        user_id=user.id,
        **data.model_dump()
    )
    
    # Обновляем статистику
    await user_repo.increment_stats(user.id, created=1)
    
    return reminder

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить напоминание по ID"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    reminder = await repo.get_by_id(reminder_id, user.id)
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    return reminder

@router.patch("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Обновить напоминание"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    reminder = await repo.update(
        reminder_id=reminder_id,
        user_id=user.id,
        **data.model_dump(exclude_none=True)
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    return reminder

@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
async def complete_reminder(
    reminder_id: int,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Отметить напоминание как выполненное"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    reminder = await repo.mark_completed(reminder_id, user.id)
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    # Обновляем статистику
    await user_repo.increment_stats(user.id, completed=1)
    
    return reminder

@router.delete("/{reminder_id}", response_model=SuccessResponse)
async def delete_reminder(
    reminder_id: int,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Удалить напоминание"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = ReminderRepository(session)
    deleted = await repo.delete(reminder_id, user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    return SuccessResponse(message="Reminder deleted")

@router.post("/parse", response_model=ParseResponse)
async def parse_text(
    data: ParseRequest,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Распарсить текст напоминания (извлечь время)"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    timezone = user.timezone if user else "Europe/Moscow"
    language = user.language if user else "ru"
    
    result = parse_reminder_text(data.text, timezone, language)
    
    return ParseResponse(
        title=result.title,
        remind_at=result.remind_at,
        confidence=result.confidence,
        is_relative=result.is_relative
    )