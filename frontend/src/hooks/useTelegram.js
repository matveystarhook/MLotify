import { useEffect, useState, useCallback } from 'react';

const tg = window.Telegram?.WebApp;

export function useTelegram() {
  const [isReady, setIsReady] = useState(false);
  const [user, setUser] = useState(null);
  const [colorScheme, setColorScheme] = useState('dark');

  useEffect(() => {
    if (!tg) {
      // Mock для разработки вне Telegram
      setUser({
        id: 123456789,
        first_name: 'Тест',
        last_name: 'User',
        username: 'testuser',
        language_code: 'ru'
      });
      setIsReady(true);
      return;
    }

    // Инициализация
    tg.ready();
    tg.expand();
    
    // Устанавливаем тёмную тему
    if (tg.setHeaderColor) {
      tg.setHeaderColor('#000000');
    }
    if (tg.setBackgroundColor) {
      tg.setBackgroundColor('#000000');
    }

    // Получаем данные пользователя
    if (tg.initDataUnsafe?.user) {
      setUser(tg.initDataUnsafe.user);
    }

    setColorScheme(tg.colorScheme || 'dark');
    setIsReady(true);

    // Слушаем изменение темы
    const handleThemeChanged = () => {
      setColorScheme(tg.colorScheme || 'dark');
    };

    tg.onEvent('themeChanged', handleThemeChanged);

    return () => {
      tg.offEvent('themeChanged', handleThemeChanged);
    };
  }, []);

  const showBackButton = useCallback((onClick) => {
    if (!tg?.BackButton) return;
    tg.BackButton.onClick(onClick);
    tg.BackButton.show();
  }, []);

  const hideBackButton = useCallback(() => {
    if (!tg?.BackButton) return;
    tg.BackButton.hide();
  }, []);

  const showMainButton = useCallback((text, onClick) => {
    if (!tg?.MainButton) return;
    tg.MainButton.setText(text);
    tg.MainButton.onClick(onClick);
    tg.MainButton.show();
  }, []);

  const hideMainButton = useCallback(() => {
    if (!tg?.MainButton) return;
    tg.MainButton.hide();
  }, []);

  const hapticFeedback = useCallback((type = 'impact') => {
    if (!tg?.HapticFeedback) return;
    
    switch (type) {
      case 'impact':
        tg.HapticFeedback.impactOccurred('medium');
        break;
      case 'notification':
        tg.HapticFeedback.notificationOccurred('success');
        break;
      case 'selection':
        tg.HapticFeedback.selectionChanged();
        break;
      case 'error':
        tg.HapticFeedback.notificationOccurred('error');
        break;
      default:
        tg.HapticFeedback.impactOccurred('light');
    }
  }, []);

  const getInitData = useCallback(() => {
    return tg?.initData || '';
  }, []);

  const close = useCallback(() => {
    if (tg) tg.close();
  }, []);

  return {
    tg,
    isReady,
    user,
    colorScheme,
    showBackButton,
    hideBackButton,
    showMainButton,
    hideMainButton,
    hapticFeedback,
    getInitData,
    close,
  };
}

export default useTelegram;