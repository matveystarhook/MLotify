# backend/bot/handlers/settings_handlers.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.database import async_session
from database.repositories.user_repo import UserRepository

router = Router()

# Доступные языки
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "uk": "🇺🇦 Українська"
}

# Популярные часовые пояса
TIMEZONES = {
    "Europe/Moscow": "🇷🇺 Москва (UTC+3)",
    "Europe/Kiev": "🇺🇦 Киев (UTC+2)",
    "Europe/Minsk": "🇧🇾 Минск (UTC+3)",
    "Asia/Almaty": "🇰🇿 Алматы (UTC+6)",
    "Asia/Tashkent": "🇺🇿 Ташкент (UTC+5)",
    "Europe/London": "🇬🇧 Лондон (UTC+0)",
    "America/New_York": "🇺🇸 Нью-Йорк (UTC-5)",
}

THEMES = {
    "auto": "🌗 Авто",
    "light": "☀️ Светлая",
    "dark": "🌙 Тёмная"
}

class SettingsStates(StatesGroup):
    waiting_for_timezone = State()

@router.callback_query(F.data == "settings")
@router.message(Command("settings"))
async def show_settings(event: Message | CallbackQuery):
    """Показать настройки"""
    
    if isinstance(event, CallbackQuery):
        message = event.message
        user_id = event.from_user.id
        await event.answer()
        edit = True
    else:
        message = event
        user_id = event.from_user.id
        edit = False
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(user_id)
        
        if not user:
            return
        
        lang = user.language
        
        text = f"""
⚙️ <b>Настройки</b>

🌐 Язык: <b>{LANGUAGES.get(user.language, user.language)}</b>
🕐 Часовой пояс: <b>{user.timezone}</b>
🎨 Тема: <b>{THEMES.get(user.theme, user.theme)}</b>
🔔 Уведомления: <b>{'Вкл' if user.notifications_enabled else 'Выкл'}</b>

Выбери, что изменить:
"""
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🌐 Язык", callback_data="settings_language")
        builder.button(text="🕐 Часовой пояс", callback_data="settings_timezone")
        builder.button(text="🎨 Тема", callback_data="settings_theme")
        builder.button(
            text=f"🔔 {'Выкл' if user.notifications_enabled else 'Вкл'} уведомления",
            callback_data="settings_notifications"
        )
        builder.button(text="◀️ Назад", callback_data="back_to_main")
        builder.adjust(2, 2, 1)
        
        if edit:
            await message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "settings_language")
async def settings_language(callback: CallbackQuery):
    """Выбор языка"""
    
    text = "🌐 <b>Выбери язык:</b>"
    
    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=f"set_lang_{code}")
    builder.button(text="◀️ Назад", callback_data="settings")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery):
    """Установка языка"""
    
    lang_code = callback.data.split("_")[2]
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            await user_repo.update_settings(user.id, language=lang_code)
    
    await callback.answer(f"Язык изменён на {LANGUAGES.get(lang_code, lang_code)}")
    await show_settings(callback)

@router.callback_query(F.data == "settings_timezone")
async def settings_timezone(callback: CallbackQuery):
    """Выбор часового пояса"""
    
    text = "🕐 <b>Выбери часовой пояс:</b>\n\nИли напиши свой (например: Europe/Paris)"
    
    builder = InlineKeyboardBuilder()
    for tz, name in TIMEZONES.items():
        builder.button(text=name, callback_data=f"set_tz_{tz}")
    builder.button(text="◀️ Назад", callback_data="settings")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("set_tz_"))
async def set_timezone(callback: CallbackQuery):
    """Установка часового пояса"""
    
    tz = callback.data.replace("set_tz_", "")
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            await user_repo.update_settings(user.id, timezone=tz)
    
    await callback.answer(f"Часовой пояс: {tz}")
    await show_settings(callback)

@router.callback_query(F.data == "settings_theme")
async def settings_theme(callback: CallbackQuery):
    """Выбор темы"""
    
    text = "🎨 <b>Выбери тему:</b>"
    
    builder = InlineKeyboardBuilder()
    for code, name in THEMES.items():
        builder.button(text=name, callback_data=f"set_theme_{code}")
    builder.button(text="◀️ Назад", callback_data="settings")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("set_theme_"))
async def set_theme(callback: CallbackQuery):
    """Установка темы"""
    
    theme = callback.data.split("_")[2]
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            await user_repo.update_settings(user.id, theme=theme)
    
    await callback.answer(f"Тема: {THEMES.get(theme, theme)}")
    await show_settings(callback)

@router.callback_query(F.data == "settings_notifications")
async def toggle_notifications(callback: CallbackQuery):
    """Переключение уведомлений"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            new_state = not user.notifications_enabled
            await user_repo.update_settings(
                user.id, 
                notifications_enabled=new_state
            )
            
            status = "включены" if new_state else "выключены"
            await callback.answer(f"🔔 Уведомления {status}")
    
    await show_settings(callback)