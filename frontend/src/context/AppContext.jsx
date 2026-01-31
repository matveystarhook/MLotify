import { createContext, useContext, useReducer, useEffect } from 'react';
import { userApi, remindersApi, categoriesApi } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

const AppContext = createContext(null);

const initialState = {
  user: null,
  reminders: [],
  categories: [],
  stats: { active: 0, completed: 0, missed: 0, total: 0, completion_rate: 0, current_streak: 0, best_streak: 0 },
  isLoading: true,
  error: null,
};

function appReducer(state, action) {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'SET_REMINDERS':
      return { ...state, reminders: action.payload };
    case 'ADD_REMINDER':
      return { ...state, reminders: [action.payload, ...state.reminders] };
    case 'UPDATE_REMINDER':
      return {
        ...state,
        reminders: state.reminders.map((r) =>
          r.id === action.payload.id ? action.payload : r
        ),
      };
    case 'REMOVE_REMINDER':
      return {
        ...state,
        reminders: state.reminders.filter((r) => r.id !== action.payload),
      };
    case 'SET_CATEGORIES':
      return { ...state, categories: action.payload };
    case 'SET_STATS':
      return { ...state, stats: action.payload };
    case 'INIT_COMPLETE':
      return { ...state, isLoading: false };
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const { isReady } = useTelegram();

  useEffect(() => {
    if (!isReady) return;

    async function loadData() {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });

        const [userRes, remindersRes, categoriesRes, statsRes] = await Promise.allSettled([
          userApi.getMe(),
          remindersApi.getAll({ status: 'active' }),
          categoriesApi.getAll(),
          userApi.getStats(),
        ]);

        if (userRes.status === 'fulfilled') {
          dispatch({ type: 'SET_USER', payload: userRes.value.data });
        }
        if (remindersRes.status === 'fulfilled') {
          dispatch({ type: 'SET_REMINDERS', payload: remindersRes.value.data.items || [] });
        }
        if (categoriesRes.status === 'fulfilled') {
          dispatch({ type: 'SET_CATEGORIES', payload: categoriesRes.value.data || [] });
        }
        if (statsRes.status === 'fulfilled') {
          dispatch({ type: 'SET_STATS', payload: statsRes.value.data });
        }

        dispatch({ type: 'INIT_COMPLETE' });
      } catch (error) {
        console.error('Failed to load data:', error);
        dispatch({ type: 'SET_ERROR', payload: error.message });
        dispatch({ type: 'INIT_COMPLETE' });
      }
    }

    loadData();
  }, [isReady]);

  const actions = {
    async createReminder(data) {
      try {
        const res = await remindersApi.create(data);
        dispatch({ type: 'ADD_REMINDER', payload: res.data });
        
        // Обновляем статистику
        const statsRes = await userApi.getStats();
        dispatch({ type: 'SET_STATS', payload: statsRes.data });
        
        return res.data;
      } catch (error) {
        console.error('Create reminder error:', error);
        throw error;
      }
    },

    async updateReminder(id, data) {
      const res = await remindersApi.update(id, data);
      dispatch({ type: 'UPDATE_REMINDER', payload: res.data });
      return res.data;
    },

    async completeReminder(id) {
      try {
        const res = await remindersApi.complete(id);
        dispatch({ type: 'UPDATE_REMINDER', payload: res.data });
        
        // Обновляем статистику
        const statsRes = await userApi.getStats();
        dispatch({ type: 'SET_STATS', payload: statsRes.data });
        
        return res.data;
      } catch (error) {
        console.error('Complete reminder error:', error);
        throw error;
      }
    },

    async deleteReminder(id) {
      await remindersApi.delete(id);
      dispatch({ type: 'REMOVE_REMINDER', payload: id });
    },

    async updateSettings(data) {
      const res = await userApi.updateSettings(data);
      dispatch({ type: 'SET_USER', payload: res.data });
      return res.data;
    },
  };

  return (
    <AppContext.Provider value={{ state, dispatch, actions }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}