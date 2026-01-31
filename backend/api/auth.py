# backend/api/auth.py

import hmac
import hashlib
import json
import time
from urllib.parse import parse_qs, unquote
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from jose import jwt, JWTError

from config import settings

# Заголовок для передачи данных Telegram
telegram_auth_header = APIKeyHeader(
    name="X-Telegram-Init-Data",
    auto_error=False
)

@dataclass
class TelegramUser:
    """Данные пользователя из Telegram WebApp"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    photo_url: Optional[str] = None

def verify_telegram_webapp_data(init_data: str) -> Optional[TelegramUser]:
    """
    Проверяет подпись данных от Telegram WebApp.
    
    Telegram подписывает данные с помощью HMAC-SHA256.
    Секретный ключ = HMAC-SHA256(bot_token, "WebAppData")
    
    Документация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    
    try:
        # Парсим данные
        parsed_data = parse_qs(init_data)
        
        # Извлекаем hash
        received_hash = parsed_data.get("hash", [None])[0]
        if not received_hash:
            return None
        
        # Собираем data-check-string (все параметры кроме hash, отсортированные)
        data_check_parts = []
        for key, values in sorted(parsed_data.items()):
            if key != "hash":
                data_check_parts.append(f"{key}={values[0]}")
        
        data_check_string = "\n".join(data_check_parts)
        
        # Создаём секретный ключ
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Сравниваем
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None
        
        # Проверяем время (данные действительны 24 часа)
        auth_date = int(parsed_data.get("auth_date", [0])[0])
        if time.time() - auth_date > 86400:  # 24 часа
            return None
        
        # Извлекаем данные пользователя
        user_data = parsed_data.get("user", [None])[0]
        if not user_data:
            return None
        
        user_dict = json.loads(unquote(user_data))
        
        return TelegramUser(
            id=user_dict["id"],
            first_name=user_dict.get("first_name", ""),
            last_name=user_dict.get("last_name"),
            username=user_dict.get("username"),
            language_code=user_dict.get("language_code"),
            is_premium=user_dict.get("is_premium", False),
            photo_url=user_dict.get("photo_url")
        )
        
    except Exception as e:
        print(f"Ошибка верификации Telegram данных: {e}")
        return None

def create_access_token(telegram_id: int) -> str:
    """Создаёт JWT токен для пользователя"""
    
    expire = datetime.utcnow() + timedelta(hours=24)
    
    payload = {
        "sub": str(telegram_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_access_token(token: str) -> Optional[int]:
    """Проверяет JWT токен и возвращает telegram_id"""
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        telegram_id = int(payload.get("sub"))
        return telegram_id
    except JWTError:
        return None

async def get_current_user(
    init_data: Optional[str] = Security(telegram_auth_header)
) -> TelegramUser:
    """
    Dependency для получения текущего пользователя.
    Проверяет данные Telegram WebApp.
    """
    
    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram authentication required"
        )
    
    user = verify_telegram_webapp_data(init_data)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authentication data"
        )
    
    return user

# Опциональная авторизация (для публичных эндпоинтов)
async def get_optional_user(
    init_data: Optional[str] = Security(telegram_auth_header)
) -> Optional[TelegramUser]:
    """Опциональная авторизация — не выбрасывает ошибку"""
    
    if not init_data:
        return None
    
    return verify_telegram_webapp_data(init_data)