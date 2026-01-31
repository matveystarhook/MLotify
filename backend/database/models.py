# backend/database/models.py

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, DateTime, 
    ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, 
    relationship
)
from enum import Enum

class Base(DeclarativeBase):
    pass

# ===== ENUMS =====

class RepeatType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKDAYS = "weekdays"  # Пн-Пт
    CUSTOM = "custom"      # Выбранные дни недели

class ReminderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# ===== USER MODEL =====

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Settings
    language: Mapped[str] = mapped_column(String(5), default="ru")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    theme: Mapped[str] = mapped_column(String(10), default="auto")  # light/dark/auto
    
    # Stats
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_reminders_created: Mapped[int] = mapped_column(Integer, default=0)
    total_reminders_completed: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    reminders: Mapped[List["Reminder"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    categories: Mapped[List["Category"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.telegram_id}: {self.first_name}>"

# ===== CATEGORY MODEL =====

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    name: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(10), default="📌")  # Emoji
    color: Mapped[str] = mapped_column(String(7), default="#6C5CE7")  # HEX
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="categories")
    reminders: Mapped[List["Reminder"]] = relationship(
        back_populates="category"
    )
    
    def __repr__(self):
        return f"<Category {self.icon} {self.name}>"

# ===== REMINDER MODEL =====

class Reminder(Base):
    __tablename__ = "reminders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Time settings
    remind_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus), 
        default=ReminderStatus.ACTIVE
    )
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority), 
        default=Priority.MEDIUM
    )
    
    # Repeat settings
    repeat_type: Mapped[RepeatType] = mapped_column(
        SQLEnum(RepeatType), 
        default=RepeatType.NONE
    )
    repeat_days: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True
    )  # "1,2,3,4,5" для custom (пн=1, вт=2...)
    repeat_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True
    )
    
    # Notification settings
    notify_before: Mapped[int] = mapped_column(Integer, default=0)  # минут до
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="reminders")
    category: Mapped[Optional["Category"]] = relationship(back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder {self.id}: {self.title[:30]}>"

# ===== ACHIEVEMENT MODEL (Геймификация) =====

class Achievement(Base):
    __tablename__ = "achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)  # "first_reminder"
    name_ru: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[str] = mapped_column(String(100))
    description_ru: Mapped[str] = mapped_column(String(200))
    description_en: Mapped[str] = mapped_column(String(200))
    icon: Mapped[str] = mapped_column(String(10))
    points: Mapped[int] = mapped_column(Integer, default=10)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)