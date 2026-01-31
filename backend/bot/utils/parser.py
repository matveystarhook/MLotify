# backend/bot/utils/parser.py

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass
import pytz

@dataclass
class ParsedReminder:
    """Результат парсинга текста напоминания"""
    title: str
    remind_at: Optional[datetime] = None
    is_relative: bool = False  # "через 2 часа" vs "завтра в 15:00"
    confidence: float = 0.0  # Уверенность в парсинге (0-1)

class NaturalLanguageParser:
    """Парсер естественного языка для напоминаний"""
    
    # Паттерны для русского языка
    PATTERNS_RU = {
        # Относительное время
        "through_minutes": r"через\s+(\d+)\s*(?:мин(?:ут[у|ы]?)?)",
        "through_hours": r"через\s+(\d+)\s*(?:час(?:а|ов)?)",
        "through_days": r"через\s+(\d+)\s*(?:день|дня|дней)",
        
        # Конкретное время
        "at_time": r"в\s+(\d{1,2})[:.]?(\d{2})?\s*(?:час(?:а|ов)?)?",
        "at_hour": r"в\s+(\d{1,2})\s*(?:час(?:а|ов)?|:00)?(?:\s|$)",
        
        # Дни
        "today": r"\bсегодня\b",
        "tomorrow": r"\bзавтра\b",
        "day_after_tomorrow": r"\bпослезавтра\b",
        
        # Дни недели
        "monday": r"\b(?:в\s+)?понедельник\b",
        "tuesday": r"\b(?:в\s+)?вторник\b",
        "wednesday": r"\b(?:в\s+)?среду?\b",
        "thursday": r"\b(?:в\s+)?четверг\b",
        "friday": r"\b(?:в\s+)?пятницу?\b",
        "saturday": r"\b(?:в\s+)?субботу?\b",
        "sunday": r"\b(?:в\s+)?воскресенье\b",
        
        # Время суток
        "morning": r"\b(?:утром?|с\s*утра)\b",
        "afternoon": r"\b(?:днём?|после\s*обеда)\b",
        "evening": r"\b(?:вечером?)\b",
        "night": r"\b(?:ночью?)\b",
        
        # Дата
        "date": r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?",
    }
    
    PATTERNS_EN = {
        "through_minutes": r"in\s+(\d+)\s*(?:min(?:ute)?s?)",
        "through_hours": r"in\s+(\d+)\s*(?:hour?s?)",
        "through_days": r"in\s+(\d+)\s*(?:day?s?)",
        
        "at_time": r"at\s+(\d{1,2})[:.]?(\d{2})?\s*(?:am|pm|AM|PM)?",
        
        "today": r"\btoday\b",
        "tomorrow": r"\btomorrow\b",
        
        "monday": r"\b(?:on\s+)?monday\b",
        "tuesday": r"\b(?:on\s+)?tuesday\b",
        "wednesday": r"\b(?:on\s+)?wednesday\b",
        "thursday": r"\b(?:on\s+)?thursday\b",
        "friday": r"\b(?:on\s+)?friday\b",
        "saturday": r"\b(?:on\s+)?saturday\b",
        "sunday": r"\b(?:on\s+)?sunday\b",
        
        "morning": r"\b(?:in\s+the\s+)?morning\b",
        "afternoon": r"\b(?:in\s+the\s+)?afternoon\b",
        "evening": r"\b(?:in\s+the\s+)?evening\b",
        "night": r"\b(?:at\s+)?night\b",
    }
    
    WEEKDAYS = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    TIME_OF_DAY = {
        "morning": 9,
        "afternoon": 14,
        "evening": 19,
        "night": 22
    }
    
    def __init__(self, timezone: str = "Europe/Moscow", language: str = "ru"):
        self.tz = pytz.timezone(timezone)
        self.language = language
        self.patterns = self.PATTERNS_RU if language == "ru" else self.PATTERNS_EN
    
    def parse(self, text: str) -> ParsedReminder:
        """Парсит текст и извлекает время напоминания"""
        
        text_lower = text.lower().strip()
        now = datetime.now(self.tz)
        
        remind_at = None
        confidence = 0.0
        cleaned_title = text
        
        # 1. Проверяем относительное время ("через X минут/часов")
        remind_at, conf, cleaned = self._parse_relative_time(text_lower, now)
        if remind_at:
            return ParsedReminder(
                title=self._clean_title(text, cleaned),
                remind_at=remind_at,
                is_relative=True,
                confidence=conf
            )
        
        # 2. Парсим день (сегодня, завтра, день недели, дата)
        target_date, conf_date, cleaned = self._parse_date(text_lower, now)
        
        # 3. Парсим время
        target_time, conf_time, cleaned2 = self._parse_time(text_lower)
        
        # Комбинируем дату и время
        if target_date or target_time:
            if target_date is None:
                target_date = now.date()
            if target_time is None:
                target_time = now.replace(hour=12, minute=0).time()  # По умолчанию полдень
            
            remind_at = datetime.combine(target_date, target_time)
            remind_at = self.tz.localize(remind_at)
            
            # Если время уже прошло сегодня, переносим на завтра
            if remind_at <= now:
                remind_at += timedelta(days=1)
            
            confidence = max(conf_date, conf_time)
            cleaned_title = self._clean_title(text, [cleaned, cleaned2])
        
        return ParsedReminder(
            title=cleaned_title if cleaned_title else text,
            remind_at=remind_at,
            is_relative=False,
            confidence=confidence
        )
    
    def _parse_relative_time(
        self, 
        text: str, 
        now: datetime
    ) -> Tuple[Optional[datetime], float, str]:
        """Парсит 'через X минут/часов/дней'"""
        
        # Минуты
        match = re.search(self.patterns["through_minutes"], text)
        if match:
            minutes = int(match.group(1))
            remind_at = now + timedelta(minutes=minutes)
            return remind_at, 0.95, match.group(0)
        
        # Часы
        match = re.search(self.patterns["through_hours"], text)
        if match:
            hours = int(match.group(1))
            remind_at = now + timedelta(hours=hours)
            return remind_at, 0.95, match.group(0)
        
        # Дни
        match = re.search(self.patterns["through_days"], text)
        if match:
            days = int(match.group(1))
            remind_at = now + timedelta(days=days)
            return remind_at, 0.9, match.group(0)
        
        return None, 0.0, ""
    
    def _parse_date(
        self, 
        text: str, 
        now: datetime
    ) -> Tuple[Optional[datetime], float, str]:
        """Парсит дату из текста"""
        
        # Сегодня
        if re.search(self.patterns["today"], text):
            return now.date(), 0.95, "сегодня" if self.language == "ru" else "today"
        
        # Завтра
        if re.search(self.patterns["tomorrow"], text):
            return (now + timedelta(days=1)).date(), 0.95, "завтра" if self.language == "ru" else "tomorrow"
        
        # Послезавтра
        if self.language == "ru" and re.search(self.patterns["day_after_tomorrow"], text):
            return (now + timedelta(days=2)).date(), 0.95, "послезавтра"
        
        # Дни недели
        for day_name, day_num in self.WEEKDAYS.items():
            if re.search(self.patterns[day_name], text):
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                target = now + timedelta(days=days_ahead)
                return target.date(), 0.85, day_name
        
        # Дата формата DD.MM или DD.MM.YYYY
        match = re.search(self.patterns["date"], text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else now.year
            if year < 100:
                year += 2000
            try:
                target = datetime(year, month, day)
                return target.date(), 0.9, match.group(0)
            except ValueError:
                pass
        
        return None, 0.0, ""
    
    def _parse_time(self, text: str) -> Tuple[Optional[datetime], float, str]:
        """Парсит время из текста"""
        
        from datetime import time
        
        # Конкретное время "в 15:30"
        match = re.search(self.patterns["at_time"], text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            
            # Корректировка для 12-часового формата
            if hour < 12 and "pm" in text.lower():
                hour += 12
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute), 0.95, match.group(0)
        
        # Только час "в 9"
        match = re.search(self.patterns["at_hour"], text)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return time(hour, 0), 0.85, match.group(0)
        
        # Время суток
        for period, hour in self.TIME_OF_DAY.items():
            if re.search(self.patterns[period], text):
                return time(hour, 0), 0.7, period
        
        return None, 0.0, ""
    
    def _clean_title(self, original: str, patterns_to_remove) -> str:
        """Очищает название от временных паттернов"""
        
        result = original
        
        if isinstance(patterns_to_remove, str):
            patterns_to_remove = [patterns_to_remove]
        
        for pattern in patterns_to_remove:
            if pattern:
                result = re.sub(re.escape(pattern), "", result, flags=re.IGNORECASE)
        
        # Убираем лишние пробелы
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Убираем предлоги в начале и конце
        result = re.sub(r'^(в|на|к|о|об)\s+', '', result, flags=re.IGNORECASE)
        result = re.sub(r'\s+(в|на|к|о|об)$', '', result, flags=re.IGNORECASE)
        
        return result.strip()


def parse_reminder_text(
    text: str, 
    timezone: str = "Europe/Moscow",
    language: str = "ru"
) -> ParsedReminder:
    """Удобная функция для парсинга"""
    parser = NaturalLanguageParser(timezone, language)
    return parser.parse(text)