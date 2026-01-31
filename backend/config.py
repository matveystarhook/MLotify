# backend/config.py

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    WEBAPP_URL: str  # URL вашего Mini App
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./loginov_remind.db"
    
    # App
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Timezone default
    DEFAULT_TIMEZONE: str = "Europe/Moscow"
    DEFAULT_LANGUAGE: str = "ru"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()