// frontend/src/components/ReminderCard.jsx

import { motion } from 'framer-motion';
import { format, isToday, isTomorrow, isPast } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useTelegram } from '../hooks/useTelegram';
import { useApp } from '../context/AppContext';

const priorityColors = {
  low: 'bg-blue-500',
  medium: 'bg-yellow-500',
  high: 'bg-red-500',
};

const priorityBg = {
  low: 'bg-blue-50 dark:bg-blue-900/20',
  medium: 'bg-yellow-50 dark:bg-yellow-900/20',
  high: 'bg-red-50 dark:bg-red-900/20',
};

export function ReminderCard({ reminder, onPress }) {
  const { hapticFeedback } = useTelegram();
  const { actions } = useApp();
  
  const isOverdue = isPast(new Date(reminder.remind_at)) && reminder.status === 'active';
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    
    if (isToday(date)) {
      return `Сегодня в ${format(date, 'HH:mm')}`;
    }
    if (isTomorrow(date)) {
      return `Завтра в ${format(date, 'HH:mm')}`;
    }
    
    return format(date, 'd MMM в HH:mm', { locale: ru });
  };
  
  const handleComplete = async (e) => {
    e.stopPropagation();
    hapticFeedback('notification');
    await actions.completeReminder(reminder.id);
  };
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      whileTap={{ scale: 0.98 }}
      onClick={onPress}
      className={`
        relative flex items-start gap-3 p-4
        bg-white dark:bg-gray-800
        rounded-2xl shadow-card
        cursor-pointer
        ${isOverdue ? 'border-l-4 border-red-500' : ''}
        ${reminder.status === 'completed' ? 'opacity-60' : ''}
      `}
    >
      {/* Checkbox */}
      <button
        onClick={handleComplete}
        className={`
          flex-shrink-0 w-6 h-6 rounded-full
          border-2 transition-all duration-200
          flex items-center justify-center
          ${reminder.status === 'completed'
            ? 'bg-accent-500 border-accent-500 text-white'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-500'
          }
        `}
      >
        {reminder.status === 'completed' && (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className={`
          font-medium text-gray-900 dark:text-white
          ${reminder.status === 'completed' ? 'line-through text-gray-500' : ''}
        `}>
          {reminder.title}
        </h3>
        
        <div className="flex items-center gap-2 mt-1.5">
          {/* Время */}
          <span className={`
            text-sm
            ${isOverdue ? 'text-red-500 font-medium' : 'text-gray-500 dark:text-gray-400'}
          `}>
            {isOverdue ? '⚠️ ' : ''}
            {formatDate(reminder.remind_at)}
          </span>
          
          {/* Категория */}
          {reminder.category && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: reminder.category.color + '20', color: reminder.category.color }}
            >
              {reminder.category.icon} {reminder.category.name}
            </span>
          )}
        </div>
      </div>
      
      {/* Priority indicator */}
      <div className={`
        w-2 h-2 rounded-full flex-shrink-0 mt-2
        ${priorityColors[reminder.priority]}
      `} />
    </motion.div>
  );
}