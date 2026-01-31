# backend/api/routes/categories.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.database import get_session
from database.repositories.user_repo import UserRepository
from database.repositories.category_repo import CategoryRepository
from api.auth import get_current_user, TelegramUser
from api.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    SuccessResponse
)

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получить все категории пользователя"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = CategoryRepository(session)
    categories = await repo.get_user_categories(user.id)
    
    return categories

@router.post("", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Создать категорию"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = CategoryRepository(session)
    category = await repo.create(
        user_id=user.id,
        **data.model_dump()
    )
    
    return category

@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Обновить категорию"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = CategoryRepository(session)
    category = await repo.update(
        category_id=category_id,
        user_id=user.id,
        **data.model_dump(exclude_none=True)
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category

@router.delete("/{category_id}", response_model=SuccessResponse)
async def delete_category(
    category_id: int,
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Удалить категорию"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = CategoryRepository(session)
    deleted = await repo.delete(category_id, user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=400, 
            detail="Category not found or is default"
        )
    
    return SuccessResponse(message="Category deleted")

@router.post("/reorder", response_model=List[CategoryResponse])
async def reorder_categories(
    category_ids: List[int],
    telegram_user: TelegramUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Изменить порядок категорий"""
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = CategoryRepository(session)
    categories = await repo.reorder(user.id, category_ids)
    
    return categories