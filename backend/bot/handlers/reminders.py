# backend/bot/handlers/reminders.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from database.database import async_session
from database.repositories.reminder_repo import ReminderRepository
from database.repositories.user_repo import UserRepository
from database.models import ReminderStatus, Priority, RepeatType
from bot.utils.parser import parse_reminder_text

router = Router()

# ===== FSM States =====

class CreateReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_category = State()
    confirm = State()

class EditReminderStates(StatesGroup):
    waiting_for_new_text = State()
    waiting_for_new_time = State()

# ===== Тексты =====

TEXTS = {
    "ru": {
        "enter_reminder": """
📝 <b>Введи текст напоминания</b>

Можешь указать время прямо в тексте:
• "Позвонить маме завтра в 15:00"
• "Встреча через 2 часа"
• "Купить молоко в понедельник"

Или просто текст — время настроим потом.
""",
        "reminder_parsed": """
📝 <b>{title}</b>

⏰ Время: <b>{time}</b>
📅 Дата: <b>{date}</b>

Всё верно?
""",
        "enter_time": """
⏰ <b>Когда напомнить?</b>

Напиши время в любом формате:
• "через 30 минут"
• "завтра в 9:00"
• "15:30"
• "послезавтра вечером"
""",
        "reminder_created": """
✅ <b>Напоминание создано!</b>

📝 {title}
⏰ {datetime}
{category}

Я напомню тебе вовремя! 🔔
""",
        "no_reminders": "📭 У тебя пока нет активных напоминаний.",
        "your_reminders": "📋 <b>Твои напоминания:</b>\n\n",
        "reminder_completed": "✅ Отлично! Напоминание отмечено как выполненное!",
        "reminder_deleted": "🗑️ Напоминание удалено.",
        "reminder_snoozed": "⏰ Хорошо, напомню через {minutes} мин.",
        "invalid_time": "❌ Не могу понять время. Попробуй ещё раз.",
        
        "btn_confirm": "✅ Подтвердить",
        "btn_change_time": "⏰ Изменить время",
        "btn_cancel": "❌ Отмена",
        "btn_complete": "✅ Выполнено",
        "btn_delete": "🗑️ Удалить",
        "btn_edit": "✏️ Изменить",
        "btn_back": "◀️ Назад",
        "btn_add_more": "➕ Ещё напоминание",
    },
    "en": {
        "enter_reminder": """
📝 <b>Enter reminder text</b>

You can include time in the text:
• "Call mom tomorrow at 3pm"
• "Meeting in 2 hours"
• "Buy milk on Monday"

Or just text — we'll set time later.
""",
        "reminder_created": """
✅ <b>Reminder created!</b>

📝 {title}
⏰ {datetime}
{category}

I'll remind you on time! 🔔
""",
        # ... остальные переводы
    }
}

def get_text(key: str, lang: str = "ru") -> str:
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))

# ===== Быстрое добавление =====

@router.callback_query(F.data == "quick_add")
async def quick_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало быстрого добавления напоминания"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        lang = user.language if user else "ru"
    
    await state.set_state(CreateReminderStates.waiting_for_text)
    await callback.message.answer(get_text("enter_reminder", lang))
    await callback.answer()

@router.message(Command("add"))
async def cmd_add_reminder(message: Message, state: FSMContext):
    """Команда /add"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        lang = user.language if user else "ru"
    
    await state.set_state(CreateReminderStates.waiting_for_text)
    await message.answer(get_text("enter_reminder", lang))

@router.message(CreateReminderStates.waiting_for_text)
async def process_reminder_text(message: Message, state: FSMContext):
    """Обработка текста напоминания"""
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        timezone = user.timezone
        
        # Парсим текст
        parsed = parse_reminder_text(message.text, timezone, lang)
        
        # Сохраняем в состояние
        await state.update_data(
            title=parsed.title,
            original_text=message.text,
            timezone=timezone,
            user_id=user.id,
            lang=lang
        )
        
        if parsed.remind_at and parsed.confidence > 0.5:
            # Время распознано — показываем подтверждение
            await state.update_data(remind_at=parsed.remind_at.isoformat())
            
            text = get_text("reminder_parsed", lang).format(
                title=parsed.title,
                time=parsed.remind_at.strftime("%H:%M"),
                date=parsed.remind_at.strftime("%d.%m.%Y")
            )
            
            builder = InlineKeyboardBuilder()
            builder.button(
                text=get_text("btn_confirm", lang),
                callback_data="confirm_reminder"
            )
            builder.button(
                text=get_text("btn_change_time", lang),
                callback_data="change_time"
            )
            builder.button(
                text=get_text("btn_cancel", lang),
                callback_data="cancel_reminder"
            )
            builder.adjust(1)
            
            await state.set_state(CreateReminderStates.confirm)
            await message.answer(text, reply_markup=builder.as_markup())
        else:
            # Время не распознано — просим ввести
            await state.set_state(CreateReminderStates.waiting_for_time)
            await message.answer(get_text("enter_time", lang))

@router.message(CreateReminderStates.waiting_for_time)
async def process_reminder_time(message: Message, state: FSMContext):
    """Обработка времени напоминания"""
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    timezone = data.get("timezone", "Europe/Moscow")
    
    # Парсим время
    parsed = parse_reminder_text(message.text, timezone, lang)
    
    if parsed.remind_at:
        await state.update_data(remind_at=parsed.remind_at.isoformat())
        
        text = get_text("reminder_parsed", lang).format(
            title=data.get("title", ""),
            time=parsed.remind_at.strftime("%H:%M"),
            date=parsed.remind_at.strftime("%d.%m.%Y")
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("btn_confirm", lang), callback_data="confirm_reminder")
        builder.button(text=get_text("btn_change_time", lang), callback_data="change_time")
        builder.button(text=get_text("btn_cancel", lang), callback_data="cancel_reminder")
        builder.adjust(1)
        
        await state.set_state(CreateReminderStates.confirm)
        await message.answer(text, reply_markup=builder.as_markup())
    else:
        await message.answer(get_text("invalid_time", lang))

@router.callback_query(F.data == "confirm_reminder")
async def confirm_reminder(callback: CallbackQuery, state: FSMContext):
    """Подтверждение создания напоминания"""
    
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    async with async_session() as session:
        repo = ReminderRepository(session)
        
        remind_at = datetime.fromisoformat(data["remind_at"])
        
        reminder = await repo.create(
            user_id=data["user_id"],
            title=data["title"],
            remind_at=remind_at
        )
        
        # Обновляем статистику пользователя
        user_repo = UserRepository(session)
        await user_repo.increment_stats(data["user_id"], created=1)
    
    text = get_text("reminder_created", lang).format(
        title=reminder.title,
        datetime=remind_at.strftime("%d.%m.%Y в %H:%M"),
        category=""
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_add_more", lang), callback_data="quick_add")
    builder.button(text=get_text("btn_back", lang), callback_data="back_to_main")
    builder.adjust(1)
    
    await state.clear()
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer("✅")

@router.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery, state: FSMContext):
    """Изменение времени"""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    await state.set_state(CreateReminderStates.waiting_for_time)
    await callback.message.answer(get_text("enter_time", lang))
    await callback.answer()

@router.callback_query(F.data == "cancel_reminder")
async def cancel_reminder(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")

# ===== Список напоминаний =====

@router.callback_query(F.data == "my_reminders")
@router.message(Command("list"))
async def show_reminders(event: Message | CallbackQuery, state: FSMContext):
    """Показать список напоминаний"""
    
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
        
        repo = ReminderRepository(session)
        reminders = await repo.get_user_reminders(
            user_id=user.id,
            status=ReminderStatus.ACTIVE,
            limit=10
        )
        
        if not reminders:
            builder = InlineKeyboardBuilder()
            builder.button(text="➕ Создать напоминание", callback_data="quick_add")
            
            await message.answer(
                get_text("no_reminders", lang),
                reply_markup=builder.as_markup()
            )
            return
        
        text = get_text("your_reminders", lang)
        builder = InlineKeyboardBuilder()
        
        for i, rem in enumerate(reminders, 1):
            priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}
            emoji = priority_emoji.get(rem.priority.value, "📌")
            
            time_str = rem.remind_at.strftime("%d.%m %H:%M")
            text += f"{emoji} <b>{rem.title[:30]}</b>\n"
            text += f"    ⏰ {time_str}\n\n"
            
            # Кнопка для каждого напоминания
            builder.button(
                text=f"{emoji} {rem.title[:20]}...",
                callback_data=f"view_reminder_{rem.id}"
            )
        
        builder.button(text="➕ Добавить", callback_data="quick_add")
        builder.button(text="◀️ Назад", callback_data="back_to_main")
        builder.adjust(1)
        
        await message.answer(text, reply_markup=builder.as_markup())

# ===== Детали напоминания =====

@router.callback_query(F.data.startswith("view_reminder_"))
async def view_reminder(callback: CallbackQuery):
    """Просмотр деталей напоминания"""
    
    reminder_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        
        repo = ReminderRepository(session)
        reminder = await repo.get_by_id(reminder_id, user.id)
        
        if not reminder:
            await callback.answer("Напоминание не найдено", show_alert=True)
            return
        
        priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}
        emoji = priority_emoji.get(reminder.priority.value, "📌")
        
        text = f"""
{emoji} <b>{reminder.title}</b>

⏰ {reminder.remind_at.strftime("%d.%m.%Y в %H:%M")}
"""
        
        if reminder.description:
            text += f"\n📋 {reminder.description}"
        
        if reminder.category:
            text += f"\n\n{reminder.category.icon} {reminder.category.name}"
        
        if reminder.repeat_type != RepeatType.NONE:
            repeat_text = {
                RepeatType.DAILY: "🔁 Ежедневно",
                RepeatType.WEEKLY: "🔁 Еженедельно",
                RepeatType.MONTHLY: "🔁 Ежемесячно",
                RepeatType.WEEKDAYS: "🔁 По будням"
            }
            text += f"\n{repeat_text.get(reminder.repeat_type, '')}"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Выполнено", callback_data=f"complete_{reminder.id}")
        builder.button(text="✏️ Изменить", callback_data=f"edit_{reminder.id}")
        builder.button(text="🗑️ Удалить", callback_data=f"delete_{reminder.id}")
        builder.button(text="◀️ Назад", callback_data="my_reminders")
        builder.adjust(1, 2, 1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()

# ===== Действия с напоминаниями =====

@router.callback_query(F.data.startswith("complete_"))
async def complete_reminder(callback: CallbackQuery):
    """Отметить напоминание выполненным"""
    
    reminder_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        
        repo = ReminderRepository(session)
        reminder = await repo.mark_completed(reminder_id, user.id)
        
        if reminder:
            await user_repo.increment_stats(user.id, completed=1)
            
            await callback.message.edit_text(
                f"✅ <b>Выполнено!</b>\n\n<s>{reminder.title}</s>\n\n🎉 Отличная работа!",
                reply_markup=None
            )
            await callback.answer("Молодец! 🎉")
        else:
            await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delete_"))
async def delete_reminder(callback: CallbackQuery):
    """Удалить напоминание"""
    
    reminder_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        
        repo = ReminderRepository(session)
        deleted = await repo.delete(reminder_id, user.id)
        
        if deleted:
            await callback.message.edit_text(
                get_text("reminder_deleted", lang),
                reply_markup=None
            )
            await callback.answer("Удалено")
        else:
            await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("snooze_"))
async def snooze_reminder(callback: CallbackQuery):
    """Отложить напоминание"""
    
    parts = callback.data.split("_")
    reminder_id = int(parts[1])
    minutes = int(parts[2])
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        
        repo = ReminderRepository(session)
        new_time = datetime.utcnow() + timedelta(minutes=minutes)
        
        reminder = await repo.update(
            reminder_id=reminder_id,
            user_id=user.id,
            remind_at=new_time,
            is_notified=False
        )
        
        if reminder:
            await callback.message.edit_text(
                get_text("reminder_snoozed", lang).format(minutes=minutes),
                reply_markup=None
            )
            await callback.answer(f"⏰ +{minutes} мин")
        else:
            await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    from bot.handlers.start import get_main_keyboard, get_text as get_start_text
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        
        if user:
            lang = user.language
            reminder_repo = ReminderRepository(session)
            stats = await reminder_repo.get_stats(user.id)
            
            text = get_start_text("welcome_back", lang).format(
                name=user.first_name,
                active=stats["active"]
            )
            
            keyboard = get_main_keyboard(lang)
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard.as_markup()
            )
    
    await callback.answer()

# ===== Обработка любого текста как напоминания =====

@router.message(F.text)
async def handle_any_text(message: Message, state: FSMContext):
    """Обрабатываем любой текст как потенциальное напоминание"""
    
    current_state = await state.get_state()
    
    # Если уже в процессе создания — не вмешиваемся
    if current_state:
        return
    
    # Пробуем распознать как напоминание
    async with async_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        lang = user.language
        timezone = user.timezone
        
        parsed = parse_reminder_text(message.text, timezone, lang)
        
        # Если распознали время — предлагаем создать напоминание
        if parsed.remind_at and parsed.confidence > 0.6:
            await state.update_data(
                title=parsed.title,
                remind_at=parsed.remind_at.isoformat(),
                user_id=user.id,
                lang=lang,
                timezone=timezone
            )
            
            text = f"""
💡 Похоже на напоминание!

📝 <b>{parsed.title}</b>
⏰ {parsed.remind_at.strftime("%d.%m.%Y в %H:%M")}

Создать напоминание?
"""
            
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Да, создать", callback_data="confirm_reminder")
            builder.button(text="❌ Нет", callback_data="cancel_reminder")
            builder.adjust(2)
            
            await state.set_state(CreateReminderStates.confirm)
            await message.answer(text, reply_markup=builder.as_markup())