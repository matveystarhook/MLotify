import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../hooks/useTelegram';
import { format, addHours, addDays, setHours, setMinutes, startOfTomorrow } from 'date-fns';

const quickTimes = [
  { label: '30 мин', icon: '⚡', getValue: () => addHours(new Date(), 0.5) },
  { label: '1 час', icon: '🕐', getValue: () => addHours(new Date(), 1) },
  { label: '3 часа', icon: '🕒', getValue: () => addHours(new Date(), 3) },
  { label: 'Завтра 9:00', icon: '🌅', getValue: () => setHours(setMinutes(startOfTomorrow(), 0), 9) },
  { label: 'Завтра 18:00', icon: '🌆', getValue: () => setHours(setMinutes(startOfTomorrow(), 0), 18) },
  { label: 'Через неделю', icon: '📅', getValue: () => addDays(new Date(), 7) },
];

const priorities = [
  { id: 'low', label: 'Низкий', color: 'from-blue-500 to-cyan-500', glow: 'glow-blue' },
  { id: 'medium', label: 'Средний', color: 'from-amber-500 to-orange-500', glow: '' },
  { id: 'high', label: 'Высокий', color: 'from-rose-500 to-pink-500', glow: 'glow-pink' },
];

export function Create() {
  const navigate = useNavigate();
  const { state, actions } = useApp();
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();
  const inputRef = useRef(null);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [remindAt, setRemindAt] = useState(null);
  const [priority, setPriority] = useState('medium');
  const [categoryId, setCategoryId] = useState(null);
  const [customDate, setCustomDate] = useState('');
  const [customTime, setCustomTime] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    showBackButton(() => navigate(-1));
    setTimeout(() => inputRef.current?.focus(), 100);
    return () => hideBackButton();
  }, []);

  useEffect(() => {
    if (customDate && customTime) {
      const dateTime = new Date(`${customDate}T${customTime}`);
      if (!isNaN(dateTime.getTime())) {
        setRemindAt(dateTime);
      }
    }
  }, [customDate, customTime]);

  const handleQuickTime = (option) => {
    hapticFeedback('impact');
    setRemindAt(option.getValue());
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('Введите название');
      hapticFeedback('error');
      return;
    }
    if (!remindAt) {
      setError('Выберите время');
      hapticFeedback('error');
      return;
    }

    setError('');
    setIsLoading(true);
    hapticFeedback('notification');

    try {
      await actions.createReminder({
        title: title.trim(),
        description: description.trim() || null,
        remind_at: remindAt.toISOString(),
        priority,
        category_id: categoryId,
      });
      navigate('/');
    } catch (err) {
      console.error('Create error:', err);
      setError('Ошибка создания. Попробуйте снова.');
      hapticFeedback('error');
    }
    setIsLoading(false);
  };

  const isValid = title.trim() && remindAt;

  return (
    <div className="min-h-screen pb-8 relative">
      {/* Космический фон */}
      <div className="cosmic-bg" />
      <div className="nebula" />

      {/* Header */}
      <header className="sticky top-0 z-20 glass-strong">
        <div className="px-5 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-white animate-fade-in">
            ✨ Новое напоминание
          </h1>
          <button
            onClick={handleSubmit}
            disabled={!isValid || isLoading}
            className={`px-5 py-2 rounded-xl text-sm font-semibold
                       transition-all duration-300 active:scale-95
                       ${isValid && !isLoading
                         ? 'gradient-purple text-white glow-purple'
                         : 'glass-button text-white/30'
                       }`}
          >
            {isLoading ? '...' : 'Готово'}
          </button>
        </div>
      </header>

      <main className="px-5 py-6 space-y-6 relative z-10">
        {/* Error */}
        {error && (
          <div className="glass-card p-4 border-rose-500/50 animate-shake">
            <p className="text-rose-400 text-sm text-center">{error}</p>
          </div>
        )}

        {/* Title */}
        <div className="animate-slide-up">
          <label className="block text-sm font-medium text-white/50 mb-3 px-1">
            Что нужно сделать?
          </label>
          <input
            ref={inputRef}
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Например: Позвонить маме"
            className="w-full px-5 py-4 rounded-2xl glass-input text-white text-lg
                       placeholder-white/30"
          />
        </div>

        {/* Description */}
        <div className="animate-slide-up delay-100">
          <label className="block text-sm font-medium text-white/50 mb-3 px-1">
            Описание <span className="text-white/30">(опционально)</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Добавьте детали..."
            rows={3}
            className="w-full px-5 py-4 rounded-2xl glass-input text-white resize-none
                       placeholder-white/30"
          />
        </div>

        {/* Time Selection */}
        <div className="animate-slide-up delay-200">
          <label className="block text-sm font-medium text-white/50 mb-3 px-1">
            ⏰ Когда напомнить?
          </label>

          {/* Selected time display */}
          {remindAt && (
            <div className="glass-card p-4 mb-4 flex items-center justify-between animate-scale-in">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl gradient-purple flex items-center justify-center">
                  <span className="text-xl">📅</span>
                </div>
                <div>
                  <div className="text-white font-semibold">
                    {format(remindAt, 'd MMMM yyyy')}
                  </div>
                  <div className="text-violet-400 text-sm">
                    {format(remindAt, 'HH:mm')}
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  setRemindAt(null);
                  setCustomDate('');
                  setCustomTime('');
                }}
                className="text-rose-400 text-sm font-medium px-3 py-1 rounded-lg
                           glass-button active:scale-95"
              >
                Изменить
              </button>
            </div>
          )}

          {/* Quick options */}
          {!remindAt && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                {quickTimes.map((option, idx) => (
                  <button
                    key={option.label}
                    onClick={() => handleQuickTime(option)}
                    className="glass-card p-4 flex items-center gap-3
                               active:scale-95 transition-all duration-300 animate-scale-in"
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <span className="text-2xl">{option.icon}</span>
                    <div className="text-left">
                      <div className="text-white text-sm font-medium">{option.label}</div>
                      <div className="text-white/40 text-xs">
                        {format(option.getValue(), 'HH:mm')}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Custom date/time */}
              <div className="glass-card p-4 animate-slide-up delay-300">
                <div className="text-sm text-white/50 mb-3">Или выберите точное время:</div>
                <div className="flex gap-3">
                  <input
                    type="date"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    className="flex-1 px-4 py-3 rounded-xl glass-input text-white"
                  />
                  <input
                    type="time"
                    value={customTime}
                    onChange={(e) => setCustomTime(e.target.value)}
                    className="w-28 px-4 py-3 rounded-xl glass-input text-white"
                  />
                </div>
              </div>
            </>
          )}
        </div>

        {/* Priority */}
        <div className="animate-slide-up delay-300">
          <label className="block text-sm font-medium text-white/50 mb-3 px-1">
            🎯 Приоритет
          </label>
          <div className="grid grid-cols-3 gap-3">
            {priorities.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  hapticFeedback('selection');
                  setPriority(p.id);
                }}
                className={`py-3.5 rounded-xl font-medium text-sm
                           transition-all duration-300 active:scale-95
                           ${priority === p.id
                             ? `bg-gradient-to-r ${p.color} text-white ${p.glow}`
                             : 'glass-button text-white/60'
                           }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Categories */}
        {state.categories.length > 0 && (
          <div className="animate-slide-up delay-400">
            <label className="block text-sm font-medium text-white/50 mb-3 px-1">
              📁 Категория
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  hapticFeedback('selection');
                  setCategoryId(null);
                }}
                className={`px-4 py-2.5 rounded-xl text-sm font-medium
                           transition-all duration-300 active:scale-95
                           ${!categoryId
                             ? 'gradient-purple text-white'
                             : 'glass-button text-white/60'
                           }`}
              >
                Без категории
              </button>
              {state.categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    hapticFeedback('selection');
                    setCategoryId(cat.id);
                  }}
                  className={`px-4 py-2.5 rounded-xl text-sm font-medium
                             transition-all duration-300 active:scale-95
                             ${categoryId === cat.id
                               ? 'text-white'
                               : 'glass-button text-white/60'
                             }`}
                  style={{
                    background: categoryId === cat.id
                      ? `linear-gradient(135deg, ${cat.color}, ${cat.color}dd)`
                      : undefined,
                  }}
                >
                  {cat.icon} {cat.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-6 animate-slide-up delay-500">
          <button
            onClick={handleSubmit}
            disabled={!isValid || isLoading}
            className={`w-full py-4 rounded-2xl text-lg font-semibold
                       transition-all duration-300 active:scale-95
                       flex items-center justify-center gap-3
                       ${isValid && !isLoading
                         ? 'gradient-purple text-white glow-purple'
                         : 'glass-button text-white/30'
                       }`}
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Создаю...
              </>
            ) : (
              <>
                <span>✨</span>
                Создать напоминание
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}