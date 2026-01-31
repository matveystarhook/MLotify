from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.database import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.reminder_repo import ReminderRepository
from config import settings

router = Router()

# ===== ТЕКСТЫ =====
TEXTS = {
    "ru": {
        "welcome_new": """
🚀 <b>Добро пожаловать в LoginovRemind!</b>

Я твой персональный помощник, который поможет тебе:

✨ Создавать напоминания голосом или текстом
⏰ Получать уведомления вовремя
📊 Отслеживать свою продуктивность
🔥 Поддерживать серии выполненных задач

<i>Нажми кнопку ниже, чтобы открыть приложение!</i>
""",
        "welcome_back": """
👋 <b>С возвращением, {name}!</b>

📊 <b>Твоя статистика:</b>
├ 📝 Активных: <b>{active}</b>
├ ✅ Выполнено: <b>{completed}</b>
└ 🔥 Серия: <b>{streak}</b> дней

<i>Что хочешь сделать?</i>
""",
        "help": """
📖 <b>Как пользоваться ботом</b>

<b>🎯 Быстрое создание:</b>
Просто напиши текст напоминания!
<i>Примеры:</i>
• "Позвонить маме завтра в 15:00"
• "Встреча через 2 часа"
• "Купить молоко в понедельник"

<b>📱 Приложение:</b>
Открой полноценное приложение для удобного управления!

<b>⚡ Команды:</b>
/start — Главное меню
/add — Добавить напоминание
/list — Список напоминаний
/stats — Твоя статистика
/settings — Настройки
""",
        "stats": """
📊 <b>Твоя статистика</b>

├ 📝 Активных напоминаний: <b>{active}</b>
├ ✅ Выполнено всего: <b>{completed}</b>
├ ❌ Пропущено: <b>{missed}</b>
├ 🔥 Текущая серия: <b>{streak}</b> дней
└ 🏆 Лучшая серия: <b>{best_streak}</b> дней

<b>📈 Успешность:</b> {rate}%
""",
        "no_reminders": """
📭 <b>У тебя пока нет активных напоминаний</b>

Создай первое напоминание:
• Напиши мне текст, например: <i>"Позвонить маме в 18:00"</i>
• Или нажми кнопку ➕ <b>Новое напоминание</b>
""",
        "reminder_created": """
✅ <b>Напоминание создано!</b>

📝 {title}
⏰ {time}
{category}

Я напомню тебе вовремя! 🔔
""",
        "btn_open_app": "🚀 Открыть приложение",
        "btn_quick_add": "➕ Новое напоминание",
        "btn_my_reminders": "📋 Мои напоминания",
        "btn_stats": "📊 Статистика",
        "btn_settings": "⚙️ Настройки",
        "btn_help": "❓ Помощь",
    },
    "en": {
        "welcome_new": """
🚀 <b>Welcome to LoginovRemind!</b>

I'm your personal assistant that will help you:

✨ Create reminders by voice or text
⏰ Get notifications on time
📊 Track your productivity
🔥 Maintain completion streaks

<i>Click the button below to open the app!</i>
""",
        "welcome_back": """
👋 <b>Welcome back, {name}!</b>

📊 <b>Your stats:</b>
├ 📝 Active: <b>{active}</b>
├ ✅ Completed: <b>{completed}</b>
└ 🔥 Streak: <b>{streak}</b> days

<i>What would you like to do?</i>
""",
        "btn_open_app": "🚀 Open App",
        "btn_quick_add": "➕ New Reminder",
        "btn_my_reminders": "📋 My Reminders",
        "btn_stats": "📊 Statistics",
        "btn_settings": "⚙️ Settings",
        "btn_help": "❓ Help",
    }
}

def get_text(key: str, lang: str = "ru") -> str:
    """Получить текст на нужном языке"""
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))

def get_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Главная клавиатура с Web App"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка Web App (главная)
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_open_app", lang),
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    
    # Быстрые действия
    builder.row(
        InlineKeyboardButton(text=get_text("btn_quick_add", lang), callback_data="quick_add"),
        InlineKeyboardButton(text=get_text("btn_my_reminders", lang), callback_data="my_reminders")
    )
    
    builder.row(
        InlineKeyboardButton(text=get_text("btn_stats", lang), callback_data="stats"),
        InlineKeyboardButton(text=get_text("btn_settings", lang), callback_data="settings")
    )
    
    builder.row(
        InlineKeyboardButton(text=get_text("btn_help", lang), callback_data="help")
    )
    
    return builder.as_markup()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        
        user, is_new = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            last_name=message.from_user.last_name
        )
        
        lang = user.language
        
        if is_new:
            text = get_text("welcome_new", lang)
        else:
            reminder_repo = ReminderRepository(session)
            stats = await reminder_repo.get_stats(user.id)
            
            text = get_text("welcome_back", lang).format(
                name=user.first_name,
                active=stats["active"],
                completed=stats["completed"],
                streak=user.current_streak
            )
        
        await message.answer(
            text=text,
            reply_markup=get_main_keyboard(lang)
        )

@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(event: Message | CallbackQuery):
    """Команда /help"""
    
    if isinstance(event, CallbackQuery):
        message = event.message
        await event.answer()
    else:
        message = event
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(event.from_user.id)
        lang = user.language if user else "ru"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="back_to_main")
    
    await message.answer(
        text=get_text("help", lang),
        reply_markup=builder.as_markup()
    )

@router.message(Command("stats"))
@router.callback_query(F.data == "stats")
async def cmd_stats(event: Message | CallbackQuery):
    """Статистика пользователя"""
    
    if isinstance(event, CallbackQuery):
        message = event.message
        user_id = event.from_user.id
        await event.answer()
    else:
        message = event
        user_id = event.from_user.id
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(user_id)
        
        if not user:
            return
        
        lang = user.language
        
        reminder_repo = ReminderRepository(session)
        stats = await reminder_repo.get_stats(user.id)
        
        # Вычисляем успешность
        total = stats["completed"] + stats["missed"]
        rate = round(stats["completed"] / total * 100) if total > 0 else 0
        
        text = get_text("stats", lang).format(
            active=stats["active"],
            completed=stats["completed"],
            missed=stats["missed"],
            streak=user.current_streak,
            best_streak=user.best_streak,
            rate=rate
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_main")
        
        if isinstance(event, CallbackQuery):
            await message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            lang = user.language
            reminder_repo = ReminderRepository(session)
            stats = await reminder_repo.get_stats(user.id)
            
            text = get_text("welcome_back", lang).format(
                name=user.first_name,
                active=stats["active"],
                completed=stats["completed"],
                streak=user.current_streak
            )
            
            await callback.message.edit_text(
                text=text,
                reply_markup=get_main_keyboard(lang)
            )
    
    await callback.answer()