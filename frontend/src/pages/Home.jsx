import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../hooks/useTelegram';
import { format, isToday, isTomorrow, isPast, differenceInMinutes } from 'date-fns';
import { ru } from 'date-fns/locale';

// Компонент звёзд
function Stars() {
  const stars = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 2 + Math.random() * 3,
      delay: Math.random() * 5,
      size: Math.random() * 2 + 1,
    }));
  }, []);

  return (
    <div className="stars">
      {stars.map((star) => (
        <div
          key={star.id}
          className="star"
          style={{
            left: `${star.left}%`,
            top: `${star.top}%`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            '--duration': `${star.duration}s`,
            '--delay': `${star.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

export function Home() {
  const navigate = useNavigate();
  const { state, actions } = useApp();
  const { user, hapticFeedback } = useTelegram();
  const [filter, setFilter] = useState('active');

  const filteredReminders = useMemo(() => {
    return state.reminders
      .filter((r) => {
        if (filter === 'active') return r.status === 'active';
        if (filter === 'completed') return r.status === 'completed';
        return true;
      })
      .sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at));
  }, [state.reminders, filter]);

  const handleComplete = async (id, e) => {
    e.stopPropagation();
    hapticFeedback('notification');
    await actions.completeReminder(id);
  };

  if (state.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="cosmic-bg" />
        <Stars />
        <div className="nebula" />
        <div className="flex flex-col items-center gap-4 z-10">
          <div className="w-16 h-16 rounded-full gradient-purple animate-pulse-glow flex items-center justify-center">
            <div className="w-12 h-12 rounded-full border-2 border-white/30 border-t-white animate-spin" />
          </div>
          <p className="text-white/60 text-sm">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-28 relative">
      {/* Космический фон */}
      <div className="cosmic-bg" />
      <Stars />
      <div className="nebula" />

      {/* Header */}
      <header className="sticky top-0 z-20 glass-strong">
        <div className="px-5 py-5">
          {/* Top Bar */}
          <div className="flex items-center justify-between mb-6">
            <div className="animate-slide-down">
              <p className="text-white/50 text-sm mb-1">Привет 👋</p>
              <h1 className="text-3xl font-bold gradient-text">
                {user?.first_name || 'Пользователь'}
              </h1>
            </div>

            <button
              onClick={() => navigate('/settings')}
              className="w-12 h-12 rounded-2xl glass-button flex items-center justify-center
                         active:scale-95 transition-transform"
            >
              <svg className="w-6 h-6 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="glass-card p-4 text-center animate-scale-in">
              <div className="text-3xl font-bold text-white mb-1">{state.stats?.active || 0}</div>
              <div className="text-xs text-white/40">Активных</div>
            </div>
            <div className="glass-card p-4 text-center animate-scale-in delay-100">
              <div className="text-3xl font-bold text-emerald-400 mb-1">{state.stats?.completed || 0}</div>
              <div className="text-xs text-white/40">Готово</div>
            </div>
            <div className="glass-card p-4 text-center animate-scale-in delay-200">
              <div className="text-3xl font-bold text-amber-400 mb-1">{state.stats?.current_streak || 0}</div>
              <div className="text-xs text-white/40">🔥 Серия</div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            {[
              { id: 'active', label: 'Активные' },
              { id: 'completed', label: 'Выполненные' },
              { id: 'all', label: 'Все' },
            ].map((tab, idx) => (
              <button
                key={tab.id}
                onClick={() => {
                  hapticFeedback('selection');
                  setFilter(tab.id);
                }}
                className={`px-5 py-2.5 rounded-2xl text-sm font-medium
                           transition-all duration-300 active:scale-95 animate-fade-in
                           ${filter === tab.id
                             ? 'gradient-purple text-white glow-purple'
                             : 'glass-button text-white/60'
                           }`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="px-5 pt-6 relative z-10">
        {filteredReminders.length === 0 ? (
          <EmptyState filter={filter} onCreate={() => navigate('/create')} />
        ) : (
          <div className="space-y-3">
            {filteredReminders.map((reminder, idx) => (
              <ReminderCard
                key={reminder.id}
                reminder={reminder}
                onPress={() => navigate(`/reminder/${reminder.id}`)}
                onComplete={(e) => handleComplete(reminder.id, e)}
                delay={idx * 50}
              />
            ))}
          </div>
        )}
      </main>

      {/* FAB */}
      <button
        onClick={() => {
          hapticFeedback('impact');
          navigate('/create');
        }}
        className="fixed bottom-8 right-5 w-16 h-16 rounded-3xl
                   gradient-purple glow-purple
                   flex items-center justify-center
                   active:scale-90 transition-transform duration-200
                   z-30 animate-float"
      >
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
}

// Reminder Card
function ReminderCard({ reminder, onPress, onComplete, delay = 0 }) {
  const isOverdue = isPast(new Date(reminder.remind_at)) && reminder.status === 'active';

  const priorityColors = {
    low: 'bg-blue-500',
    medium: 'bg-amber-500',
    high: 'bg-rose-500',
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    if (isToday(date)) return format(date, 'HH:mm');
    if (isTomorrow(date)) return `Завтра, ${format(date, 'HH:mm')}`;
    return format(date, 'd MMM, HH:mm', { locale: ru });
  };

  return (
    <div
      onClick={onPress}
      className="glass-card p-5 cursor-pointer active:scale-[0.98] transition-all duration-300 animate-slide-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start gap-4">
        {/* Checkbox */}
        <button
          onClick={onComplete}
          className={`w-7 h-7 rounded-full border-2 flex items-center justify-center
                     flex-shrink-0 mt-0.5 transition-all duration-300
                     ${reminder.status === 'completed'
                       ? 'bg-emerald-500 border-emerald-500 glow-green'
                       : 'border-white/30 hover:border-violet-400'
                     }`}
        >
          {reminder.status === 'completed' && (
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className={`text-lg font-semibold mb-2 line-clamp-2
                         ${reminder.status === 'completed' ? 'line-through text-white/40' : 'text-white'}`}>
            {reminder.title}
          </h3>

          <div className="flex items-center gap-3 flex-wrap">
            <span className={`text-sm flex items-center gap-1.5
                             ${isOverdue ? 'text-rose-400 font-medium' : 'text-white/50'}`}>
              {isOverdue ? '⚠️' : '🕐'} {formatTime(reminder.remind_at)}
            </span>

            {reminder.category && (
              <span className="px-3 py-1 rounded-full text-xs font-medium glass-button text-white/70">
                {reminder.category.icon} {reminder.category.name}
              </span>
            )}
          </div>
        </div>

        {/* Priority */}
        {reminder.status === 'active' && (
          <div className={`w-3 h-3 rounded-full ${priorityColors[reminder.priority]} flex-shrink-0 mt-2`} />
        )}
      </div>
    </div>
  );
}

// Empty State
function EmptyState({ filter, onCreate }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
      <div className="w-32 h-32 rounded-full glass-card flex items-center justify-center mb-8 animate-float">
        <span className="text-6xl">{filter === 'completed' ? '🎉' : '✨'}</span>
      </div>
      <h3 className="text-2xl font-bold text-white mb-3">
        {filter === 'completed' ? 'Пока пусто' : 'Нет напоминаний'}
      </h3>
      <p className="text-white/50 text-center max-w-xs mb-8">
        {filter === 'completed'
          ? 'Выполненные задачи появятся здесь'
          : 'Создай первое напоминание'}
      </p>
      {filter !== 'completed' && (
        <button
          onClick={onCreate}
          className="px-8 py-4 rounded-2xl gradient-purple text-white font-semibold
                     glow-purple active:scale-95 transition-transform"
        >
          Создать напоминание
        </button>
      )}
    </div>
  );
}