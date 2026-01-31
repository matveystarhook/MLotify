# backend/api/schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class RepeatTypeEnum(str, Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    weekdays = "weekdays"
    custom = "custom"

class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class StatusEnum(str, Enum):
    active = "active"
    completed = "completed"
    missed = "missed"
    cancelled = "cancelled"

# ===== USER SCHEMAS =====

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None

class UserSettings(BaseModel):
    language: str = "ru"
    timezone: str = "Europe/Moscow"
    notifications_enabled: bool = True
    theme: str = "auto"

class UserResponse(UserBase):
    id: int
    language: str
    timezone: str
    notifications_enabled: bool
    theme: str
    created_at: datetime
    total_reminders_created: int
    total_reminders_completed: int
    current_streak: int
    best_streak: int
    
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    language: Optional[str] = None
    timezone: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None

# ===== CATEGORY SCHEMAS =====

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: str = Field(default="📌", max_length=10)
    color: str = Field(default="#6C5CE7", pattern=r"^#[0-9A-Fa-f]{6}$")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    icon: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    order: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    is_default: bool
    order: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== REMINDER SCHEMAS =====

class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    remind_at: datetime
    category_id: Optional[int] = None
    priority: PriorityEnum = PriorityEnum.medium
    repeat_type: RepeatTypeEnum = RepeatTypeEnum.none
    repeat_days: Optional[str] = None  # "1,2,3,4,5" для кастомных дней
    repeat_end_date: Optional[datetime] = None
    notify_before: int = Field(default=0, ge=0, le=1440)  # минут до (макс 24 часа)

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    remind_at: Optional[datetime] = None
    category_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    repeat_type: Optional[RepeatTypeEnum] = None
    repeat_days: Optional[str] = None
    repeat_end_date: Optional[datetime] = None
    notify_before: Optional[int] = Field(None, ge=0, le=1440)

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    status: StatusEnum
    created_at: datetime
    completed_at: Optional[datetime]
    is_notified: bool
    notification_count: int
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True

class ReminderListResponse(BaseModel):
    items: List[ReminderResponse]
    total: int
    has_more: bool

# ===== STATS SCHEMAS =====

class StatsResponse(BaseModel):
    active: int
    completed: int
    missed: int
    total: int
    completion_rate: float  # Процент выполненных
    current_streak: int
    best_streak: int
    
class DailyStats(BaseModel):
    date: str  # "2024-01-15"
    created: int
    completed: int

class WeeklyStatsResponse(BaseModel):
    days: List[DailyStats]
    total_created: int
    total_completed: int

# ===== PARSE SCHEMAS =====

class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

class ParseResponse(BaseModel):
    title: str
    remind_at: Optional[datetime]
    confidence: float
    is_relative: bool

# ===== COMMON SCHEMAS =====

class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None